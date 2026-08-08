"""Application-level exceptions for the LLM provider layer.

These exceptions are provider-agnostic: down-stream code can catch them
without knowing whether the underlying provider is Gemini, OpenAI, etc.
"""


class LLMError(Exception):
    """Base class for all LLM provider errors."""


class LLMConfigurationError(LLMError):
    """Raised when the LLM provider is missing required configuration.

    For example, a missing API key or model name.
    """


class LLMGenerationError(LLMError):
    """Raised when the LLM provider fails to generate a response.

    Wraps provider-specific SDK/HTTP exceptions so they never leak out of
    the application boundary.
    """