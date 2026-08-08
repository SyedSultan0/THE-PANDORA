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

import os
from typing import Any

from app.llm.base import LLMProvider
from app.llm.errors import LLMConfigurationError, LLMGenerationError

DEFAULT_OPENROUTER_MODEL = "openrouter/free"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

_OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"
_OPENROUTER_MODEL_ENV = "OPENROUTER_MODEL"


class OpenRouterProvider(LLMProvider):
    """LLM provider backed by OpenRouter's OpenAI-compatible API."""

    def __init__(self, client: Any | None = None) -> None:
        """Initialize the provider.

        Args:
            client: An optional pre-configured HTTP client (e.g. an
                ``httpx.Client``). Used primarily for testing; when omitted,
                the client is created lazily on the first ``generate`` call.
        """
        self._client = client
        self._model = os.getenv(_OPENROUTER_MODEL_ENV, DEFAULT_OPENROUTER_MODEL)

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    def generate(self, prompt: str) -> str:
        """Generate text for ``prompt`` using the OpenRouter API.

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
        api_key = os.getenv(_OPENROUTER_API_KEY_ENV)

        try:
            response = client.post(
                OPENROUTER_ENDPOINT,
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
            raise LLMGenerationError(f"OpenRouter generation failed: {exc}") from exc

        if not text or not isinstance(text, str):
            raise LLMGenerationError(
                "OpenRouter returned an empty response (no text content)."
            )

        return text

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> Any:
        """Return the HTTP client, creating it lazily if not provided."""
        if self._client is not None:
            return self._client

        api_key = os.getenv(_OPENROUTER_API_KEY_ENV)
        if not api_key:
            raise LLMConfigurationError(
                f"Missing required environment variable '{_OPENROUTER_API_KEY_ENV}'. "
                "Set it (e.g. in a .env file) before using the OpenRouter provider."
            )

        # Imported lazily so the module can be unit-tested without the
        # dependency being imported at module scope.
        import httpx  # type: ignore[import-not-found]

        return httpx.Client(timeout=60)