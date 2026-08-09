"""NVIDIA NIM LLM provider.

Implements the same :class:`LLMProvider` interface as the Gemini and
OpenRouter providers so down-stream code never knows which provider is in
use.

NVIDIA exposes an OpenAI-compatible ``/chat/completions`` endpoint. This
provider uses that endpoint via the ``httpx`` client (already a project
dependency).

Configuration is read from environment variables (optionally loaded from a
``.env`` file by the caller):

* ``NVIDIA_API_KEY`` — the NVIDIA API key (required).
* ``NVIDIA_MODEL``   — the model identifier (optional, defaults to
  ``meta/llama-3.3-70b-instruct``).
"""

import logging
import os
import time
from typing import Any

from app.llm.base import LLMProvider
from app.llm.errors import LLMConfigurationError, LLMGenerationError

logger = logging.getLogger(__name__)

DEFAULT_NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"
NVIDIA_ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"

_NVIDIA_API_KEY_ENV = "NVIDIA_API_KEY"
_NVIDIA_MODEL_ENV = "NVIDIA_MODEL"


class NvidiaProvider(LLMProvider):
    """LLM provider backed by NVIDIA's OpenAI-compatible chat API."""

    def __init__(self, client: Any | None = None) -> None:
        """Initialize the provider.

        Args:
            client: An optional pre-configured HTTP client (e.g. an
                ``httpx.Client``). Used primarily for testing; when omitted,
                the client is created lazily on the first ``generate`` call.
        """
        self._client = client
        self._model = os.getenv(_NVIDIA_MODEL_ENV, DEFAULT_NVIDIA_MODEL)
        self.generate_count = 0
        self.last_generate_elapsed_s: float | None = None

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    def generate(self, prompt: str) -> str:
        """Generate text for ``prompt`` using the NVIDIA API.

        Args:
            prompt: The full prompt text.

        Returns:
            The generated text.

        Raises:
            LLMConfigurationError: If the API key is missing.
            LLMGenerationError: If the HTTP/API call fails or the response
                is malformed.
        """
        client = self._get_client()
        api_key = os.getenv(_NVIDIA_API_KEY_ENV)

        self.generate_count += 1
        start = time.perf_counter()
        try:
            response = client.post(
                NVIDIA_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"]
        except Exception as exc:  # HTTP/network/JSON/property errors isolated here
            # Log the full traceback server-side for debugging, but never
            # include the API key or auth headers in the raised message.
            logger.exception("NVIDIA generation failed")
            safe_detail = _safe_error_detail(exc)
            raise LLMGenerationError(
                f"NVIDIA generation failed: {safe_detail}"
            ) from exc
        finally:
            self.last_generate_elapsed_s = time.perf_counter() - start

        if not text or not isinstance(text, str):
            raise LLMGenerationError(
                "NVIDIA returned an empty response (no text content)."
            )

        return text

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> Any:
        """Return the HTTP client, creating it lazily if not provided."""
        if self._client is not None:
            return self._client

        api_key = os.getenv(_NVIDIA_API_KEY_ENV)
        if not api_key:
            raise LLMConfigurationError(
                f"Missing required environment variable '{_NVIDIA_API_KEY_ENV}'. "
                "Set it (e.g. in a .env file) before using the NVIDIA provider."
            )

        # Imported lazily so the module can be unit-tested without the
        # dependency being imported at module scope.
        import httpx  # type: ignore[import-not-found]

        return httpx.Client(timeout=60)


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