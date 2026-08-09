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
from app.llm.failover import FailoverLLMProvider
from app.llm.gemini import DEFAULT_GEMINI_MODEL, GeminiProvider
from app.llm.nvidia import DEFAULT_NVIDIA_MODEL, NvidiaProvider
from app.llm.openrouter import DEFAULT_OPENROUTER_MODEL, OpenRouterProvider

__all__ = [
    "DEFAULT_GEMINI_MODEL",
    "DEFAULT_NVIDIA_MODEL",
    "DEFAULT_OPENROUTER_MODEL",
    "FailoverLLMProvider",
    "GeminiProvider",
    "LLMConfigurationError",
    "LLMError",
    "LLMGenerationError",
    "LLMProvider",
    "NvidiaProvider",
    "OpenRouterProvider",
]
