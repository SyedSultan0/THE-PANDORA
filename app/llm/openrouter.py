"""OpenRouter LLM provider.

Implements the same :class:`LLMProvider` interface as the Gemini provider so
down-stream code (interview engine, generators, etc.) never knows which
provider is in use.

OpenRouter exposes an OpenAI-compatible ``/chat/completions`` endpoint. This
provider uses that endpoint via the ``httpx`` client (already a project
dependency).

Configuration is read from environment variables (optionally loaded from a
``.env`` file by the caller):

* ``OPENROUTER_API_KEY`` — the OpenRouter API key (required).
* ``OPENROUTER_MODEL``   — the model identifier (optional, defaults to
  ``openrouter/free``).
"""

import logging
import os
import time
from typing import Any

from app.llm.base import LLMProvider
from app.llm.errors import LLMConfigurationError, LLMGenerationError

logger = logging.getLogger(__name__)

DEFAULT_OPENROUTER_MODEL = "openrouter/free"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

_OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"
_OPENROUTER_MODEL_ENV = "OPENROUTER_MODEL"


class OpenRouterProvider(LLMProvider):
    """LLM provider backed by OpenRouter's OpenAI-compatible API.

    Supports multiple key/model pairs via numbered environment variables
    (``OPENROUTER_API_KEY_1`` / ``OPENROUTER_MODEL_1``, etc.) with automatic
    failover on retryable provider/network errors. Falls back to the legacy
    single-key configuration when numbered pairs are not configured.
    """

    def __init__(self, client: Any | None = None) -> None:
        """Initialize the provider.

        Args:
            client: An optional pre-configured HTTP client (e.g. an
                ``httpx.Client``). Used primarily for testing; when omitted,
                the client is created lazily on the first ``generate`` call.
        """
        self._client = client
        self._model = os.getenv(_OPENROUTER_MODEL_ENV, DEFAULT_OPENROUTER_MODEL)
        self.generate_count = 0
        self.last_generate_elapsed_s: float | None = None
        self._pairs = _discover_pairs()
        # Preserve backward compatibility for tests that inject a client
        # without configuring environment variables.
        if not self._pairs and self._client is not None:
            self._pairs = [("injected-client", self._model)]

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    def generate(self, prompt: str) -> str:
        """Generate text for ``prompt`` using the OpenRouter API.

        If multiple key/model pairs are configured, attempts them in order
        with automatic failover on retryable provider/network errors.

        Args:
            prompt: The full prompt text.

        Returns:
            The generated text.

        Raises:
            LLMConfigurationError: If no API key is configured.
            LLMGenerationError: If all configured pairs fail or the response
                is malformed.
        """
        if not self._pairs:
            raise LLMConfigurationError(
                f"Missing required environment variable '{_OPENROUTER_API_KEY_ENV}'. "
                "Set it (e.g. in a .env file) before using the OpenRouter provider."
            )

        last_error: Exception | None = None
        self.generate_count += 1
        total = len(self._pairs)
        for attempt, (api_key, model) in enumerate(self._pairs, start=1):
            client = self._get_client()
            start = time.perf_counter()
            try:
                response = client.post(
                    OPENROUTER_ENDPOINT,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                response.raise_for_status()
                data = response.json()
                text = data["choices"][0]["message"]["content"]
            except Exception as exc:  # HTTP/network/JSON/property errors isolated here
                self.last_generate_elapsed_s = time.perf_counter() - start
                last_error = exc
                if _is_retryable(exc) and attempt < total:
                    logger.warning(
                        "OpenRouter attempt %s/%s using model=%s failed with %s; "
                        "attempting next configured provider",
                        attempt,
                        total,
                        model,
                        _safe_error_detail(exc),
                    )
                    continue
                logger.warning(
                    "OpenRouter attempt %s/%s using model=%s failed with %s",
                    attempt,
                    total,
                    model,
                    _safe_error_detail(exc),
                )
                # Final attempt or non-retryable error.
                logger.exception("OpenRouter generation failed")
                safe_detail = _safe_error_detail(exc)
                raise LLMGenerationError(
                    f"OpenRouter generation failed: {safe_detail}"
                ) from exc
            finally:
                # Keep timing from the last attempted call.
                self.last_generate_elapsed_s = time.perf_counter() - start

            if not text or not isinstance(text, str):
                raise LLMGenerationError(
                    "OpenRouter returned an empty response (no text content)."
                )

            logger.info(
                "OpenRouter attempt %s/%s using model=%s succeeded",
                attempt,
                total,
                model,
            )
            return text

        # All pairs exhausted without returning.
        assert last_error is not None
        logger.warning("OpenRouter all providers exhausted")
        raise LLMGenerationError(
            f"OpenRouter generation failed: {_safe_error_detail(last_error)}"
        ) from last_error

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> Any:
        """Return the HTTP client, creating it lazily if not provided."""
        if self._client is not None:
            return self._client

        # The API key is validated by _discover_pairs() / generate().
        # Imported lazily so the module can be unit-tested without the
        # dependency being imported at module scope.
        import httpx  # type: ignore[import-not-found]

        return httpx.Client(timeout=60)


def _discover_pairs() -> list[tuple[str, str]]:
    """Discover ordered key/model pairs from environment variables.

    Prefers numbered pairs (``OPENROUTER_API_KEY_1`` / ``OPENROUTER_MODEL_1``,
    etc.). Falls back to the legacy single-key configuration. If a numbered
    key is configured but its model is missing, ``openrouter/free`` is used
    as the default for that key.
    """
    # 1. Numbered pairs take precedence.
    pairs: list[tuple[str, str]] = []
    for idx in range(1, 10):
        key = os.getenv(f"{_OPENROUTER_API_KEY_ENV}_{idx}")
        if not key:
            continue
        model = os.getenv(f"{_OPENROUTER_MODEL_ENV}_{idx}", DEFAULT_OPENROUTER_MODEL)
        pairs.append((key, model))
    if pairs:
        logger.info("Configured OpenRouter providers: %s", len(pairs))
        return pairs

    # 2. Legacy single-key configuration.
    legacy_key = os.getenv(_OPENROUTER_API_KEY_ENV)
    legacy_model = os.getenv(_OPENROUTER_MODEL_ENV, DEFAULT_OPENROUTER_MODEL)
    if legacy_key:
        logger.info("Configured OpenRouter provider: 1 (legacy)")
        return [(legacy_key, legacy_model)]
    return []


def _is_retryable(exc: Exception) -> bool:
    """Return True if the exception is a retryable provider/network error.

    Retryable: 429, 401, 403, 500, 501, 502, 503, 504, timeouts, connection
    errors. This allows failover to the next configured credential when the
    current one hits rate limits or auth issues.
    """
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        if status_code in (429, 401, 403) or status_code >= 500:
            return True
    name = type(exc).__name__.lower()
    retryable_names = ("timeout", "connectionerror", "connecterror", "readerror", "networkerror")
    if any(n in name for n in retryable_names):
        return True
    return False


def _safe_error_detail(exc: Exception) -> str:
    """Return a safe error description without API keys or auth headers.

    For HTTP errors we surface the status code and URL. For other exceptions
    we preserve the original exception message, which often contains the
    actionable detail (e.g. ``connection reset``).
    """
    status_text = getattr(exc, "status_code", None)
    url = getattr(exc, "url", None)
    parts: list[str] = []
    if status_text is not None:
        parts.append(f"HTTP {status_text}")
    if url is not None:
        parts.append(f"url={url}")
    if parts:
        parts.append(type(exc).__name__)
        return "; ".join(parts)
    return str(exc)