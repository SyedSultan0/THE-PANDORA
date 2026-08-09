"""Composite LLM provider that fails over across multiple providers.

The rest of the application depends only on :class:`LLMProvider`, so the
interview engine never knows whether a request goes to NVIDIA, OpenRouter,
or Gemini. Failover happens entirely at the LLM provider layer.
"""

import logging
import time

from app.llm.base import LLMProvider
from app.llm.errors import LLMConfigurationError, LLMGenerationError

logger = logging.getLogger(__name__)


class FailoverLLMProvider(LLMProvider):
    """Try providers in order; fall through on retryable failures.

    Providers are attempted in the order they are supplied. A provider that
    raises :class:`LLMConfigurationError` is skipped (e.g. not configured).
    A provider that raises :class:`LLMGenerationError` with a retryable
    cause (HTTP 429/5xx, timeout, connection/network error) triggers the
    next provider. Non-retryable errors are raised immediately.
    """

    def __init__(self, providers: list[LLMProvider]) -> None:
        """Initialize the failover provider.

        Args:
            providers: Ordered list of providers to try.
        """
        self._providers = list(providers)
        self.generate_count = 0
        self.last_generate_elapsed_s: float | None = None

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    def generate(self, prompt: str) -> str:
        """Generate text by trying each provider in order.

        Args:
            prompt: The full prompt text.

        Returns:
            The generated text from the first successful provider.

        Raises:
            LLMConfigurationError: If no providers are configured.
            LLMGenerationError: If all providers fail.
        """
        if not self._providers:
            raise LLMConfigurationError("No LLM providers configured.")

        last_error: Exception | None = None
        self.generate_count += 1
        total = len(self._providers)
        for attempt, provider in enumerate(self._providers, start=1):
            name = type(provider).__name__
            start = time.perf_counter()
            try:
                result = provider.generate(prompt)
                self.last_generate_elapsed_s = time.perf_counter() - start
                logger.info(
                    "Failover attempt %s/%s (%s) succeeded",
                    attempt,
                    total,
                    name,
                )
                return result
            except LLMConfigurationError as exc:
                # Provider not configured; skip to the next one.
                logger.warning(
                    "Failover attempt %s/%s (%s) not configured: %s",
                    attempt,
                    total,
                    name,
                    exc,
                )
                last_error = exc
                continue
            except LLMGenerationError as exc:
                last_error = exc
                if attempt < total and _is_retryable_generation_error(exc):
                    logger.warning(
                        "Failover attempt %s/%s (%s) failed: %s; "
                        "trying next provider",
                        attempt,
                        total,
                        name,
                        exc,
                    )
                    continue
                logger.exception(
                    "Failover attempt %s/%s (%s) failed",
                    attempt,
                    total,
                    name,
                )
                raise
            finally:
                self.last_generate_elapsed_s = time.perf_counter() - start

        assert last_error is not None
        logger.warning("All LLM providers exhausted")
        raise LLMGenerationError(
            f"All LLM providers failed: {last_error}"
        ) from last_error


def _is_retryable_generation_error(exc: Exception) -> bool:
    """Return True if the wrapped error is a retryable provider failure.

    The provider-specific error detail is embedded in the exception message
    (e.g. ``HTTP 429``, ``connection reset``, ``timed out``). We match on
    those safe markers — never on API keys or auth headers.
    """
    message = str(exc).lower()
    markers = (
        "http 429",
        "http 401",
        "http 403",
        "http 500",
        "http 501",
        "http 502",
        "http 503",
        "http 504",
        "timeout",
        "timed out",
        "connection",
        "network",
    )
    return any(marker in message for marker in markers)