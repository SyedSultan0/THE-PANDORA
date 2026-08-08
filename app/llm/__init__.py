"""LLM provider abstraction for the AI Interview Agent.

The rest of the application depends only on :class:`LLMProvider` and the
provider-agnostic exceptions; it never imports provider-specific SDKs.
"""

from app.llm.base import LLMProvider
from app.llm.errors import (
    LLMConfigurationError,
    LLMError,
    LLMGenerationError,
)
from app.llm.gemini import DEFAULT_GEMINI_MODEL, GeminiProvider

__all__ = [
    "DEFAULT_GEMINI_MODEL",
    "GeminiProvider",
    "LLMConfigurationError",
    "LLMError",
    "LLMGenerationError",
    "LLMProvider",
]