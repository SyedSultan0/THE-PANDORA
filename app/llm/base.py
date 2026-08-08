"""Provider-agnostic LLM interface.

Down-stream code (interview engine, etc.) depends only on this interface,
never on a concrete provider class or its SDK.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract interface for a text-generation LLM provider."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a text completion for the given prompt.

        Args:
            prompt: The full prompt text to send to the model.

        Returns:
            The generated response text.

        Raises:
            LLMConfigurationError: If the provider is missing required
                configuration (e.g., API key or model name).
            LLMGenerationError: If the provider fails to generate a
                response (network, SDK, or API errors).
        """