"""Google Gemini LLM provider.

All Gemini SDK imports and API calls live in this module. The rest of the
application depends only on :class:`LLMProvider` and the exceptions in
``app.llm.errors``.

Configuration is read from environment variables (optionally loaded from a
``.env`` file by the caller):

* ``GEMINI_API_KEY`` — the Gemini API key (required).
* ``GEMINI_MODEL``   — the model name (optional, defaults to
  ``gemini-2.0-flash``).
"""

import os
from typing import Any

from app.llm.base import LLMProvider
from app.llm.errors import LLMConfigurationError, LLMGenerationError

DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"

_GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
_GEMINI_MODEL_ENV = "GEMINI_MODEL"


class GeminiProvider(LLMProvider):
    """LLM provider backed by the Google Gemini API."""

    def __init__(self, client: Any | None = None) -> None:
        """Initialize the provider.

        Args:
            client: An optional pre-configured Gemini client. Used primarily
                for testing; when omitted, the client is created lazily from
                environment configuration on the first ``generate`` call.
        """
        self._client = client
        self._model = os.getenv(_GEMINI_MODEL_ENV, DEFAULT_GEMINI_MODEL)

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    def generate(self, prompt: str) -> str:
        """Generate text for ``prompt`` using the Gemini API.

        Args:
            prompt: The full prompt text.

        Returns:
            The generated text.

        Raises:
            LLMConfigurationError: If the API key is missing.
            LLMGenerationError: If the Gemini SDK/API call fails.
        """
        client = self._get_client()
        try:
            response = client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
            text = response.text
        except Exception as exc:  # SDK/API/network/property errors isolated here
            raise LLMGenerationError(f"Gemini generation failed: {exc}") from exc

        if text is None:
            raise LLMGenerationError(
                "Gemini returned an empty response (no text content)."
            )

        return text

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> Any:
        """Return the Gemini client, creating it lazily if not provided."""
        if self._client is not None:
            return self._client

        api_key = os.getenv(_GEMINI_API_KEY_ENV)
        if not api_key:
            raise LLMConfigurationError(
                f"Missing required environment variable '{_GEMINI_API_KEY_ENV}'. "
                "Set it (e.g. in a .env file) before using the Gemini provider."
            )

        # Imported lazily so the module can be unit-tested without the
        # Gemini SDK installed and so the SDK is easy to swap later.
        from google import genai  # type: ignore[import-not-found]

        return genai.Client(api_key=api_key)