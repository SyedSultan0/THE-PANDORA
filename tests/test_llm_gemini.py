"""Tests for the Gemini LLM provider and the provider abstraction.

No real API key or network calls are required — a fake client is used.
"""

import os

import pytest

from app.llm import (
    GeminiProvider,
    LLMConfigurationError,
    LLMError,
    LLMGenerationError,
    LLMProvider,
)


class FakeGenaiResponse:
    """Minimal stand-in for ``genai.types.GenerateContentResponse``."""

    def __init__(self, text: str | None) -> None:
        self.text = text


class FakeGenaiClient:
    """Minimal stand-in for ``genai.Client``."""

    def __init__(self, response: FakeGenaiResponse | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.last_model: str | None = None
        self.last_contents: str | None = None

    @property
    def models(self):
        return self

    def generate_content(self, *, model: str, contents: str) -> FakeGenaiResponse:
        self.last_model = model
        self.last_contents = contents
        if self.error is not None:
            raise self.error
        return self.response


class TestGenerateSuccess:
    """Tests for successful text generation."""

    def test_returns_generated_text(self) -> None:
        fake_client = FakeGenaiClient(response=FakeGenaiResponse("Hello, world!"))
        provider = GeminiProvider(client=fake_client)

        result = provider.generate("Say hello")

        assert result == "Hello, world!"

    def test_passes_prompt_and_model_to_sdk(self) -> None:
        fake_client = FakeGenaiClient(response=FakeGenaiResponse("ok"))
        provider = GeminiProvider(client=fake_client)

        provider.generate("Tell me a joke")

        assert fake_client.last_contents == "Tell me a joke"
        assert fake_client.last_model is not None

    def test_uses_default_model_when_env_not_set(self, monkeypatch) -> None:
        monkeypatch.delenv("GEMINI_MODEL", raising=False)
        fake_client = FakeGenaiClient(response=FakeGenaiResponse("ok"))
        provider = GeminiProvider(client=fake_client)

        provider.generate("hi")

        assert fake_client.last_model == "gemini-2.0-flash"

    def test_uses_model_from_environment(self, monkeypatch) -> None:
        monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
        fake_client = FakeGenaiClient(response=FakeGenaiResponse("ok"))
        provider = GeminiProvider(client=fake_client)

        provider.generate("hi")

        assert fake_client.last_model == "gemini-2.5-pro"


class TestMissingConfiguration:
    """Tests for missing API configuration."""

    def test_missing_api_key_raises_configuration_error(self, monkeypatch) -> None:
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        provider = GeminiProvider()  # no client injected

        with pytest.raises(LLMConfigurationError) as excinfo:
            provider.generate("hello")

        assert "GEMINI_API_KEY" in str(excinfo.value)

    def test_configuration_error_is_llm_error(self, monkeypatch) -> None:
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        provider = GeminiProvider()

        with pytest.raises(LLMError):
            provider.generate("hello")

    def test_injected_client_bypasses_api_key_check(self, monkeypatch) -> None:
        """With an injected client, no API key is required (used in tests)."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        fake_client = FakeGenaiClient(response=FakeGenaiResponse("ok"))
        provider = GeminiProvider(client=fake_client)

        result = provider.generate("hi")

        assert result == "ok"


class TestProviderFailure:
    """Tests for provider/API error handling."""

    def test_sdk_error_wrapped_in_generation_error(self) -> None:
        fake_client = FakeGenaiClient(error=RuntimeError("connection reset"))
        provider = GeminiProvider(client=fake_client)

        with pytest.raises(LLMGenerationError) as excinfo:
            provider.generate("hello")

        assert "connection reset" in str(excinfo.value)

    def test_generation_error_is_llm_error(self) -> None:
        fake_client = FakeGenaiClient(error=ValueError("bad request"))
        provider = GeminiProvider(client=fake_client)

        with pytest.raises(LLMError):
            provider.generate("hello")

    def test_raw_sdk_exception_does_not_leak(self) -> None:
        fake_client = FakeGenaiClient(error=RuntimeError("raw SDK error"))
        provider = GeminiProvider(client=fake_client)

        with pytest.raises(LLMGenerationError):
            provider.generate("hello")
        # The raw exception must not escape as its original type.
        with pytest.raises(Exception) as excinfo:
            provider.generate("hello")
        assert not isinstance(excinfo.value, RuntimeError)

    def test_none_response_text_raises_generation_error(self) -> None:
        fake_client = FakeGenaiClient(response=FakeGenaiResponse(None))
        provider = GeminiProvider(client=fake_client)

        with pytest.raises(LLMGenerationError, match="empty response"):
            provider.generate("hello")


class TestAbstraction:
    """Tests that the abstraction hides provider specifics."""

    def test_gemini_provider_is_an_llm_provider(self) -> None:
        provider = GeminiProvider(client=FakeGenaiClient(response=FakeGenaiResponse("x")))
        assert isinstance(provider, LLMProvider)

    def test_usage_through_interface_only(self) -> None:
        """Downstream code can use only the LLMProvider interface."""
        fake_client = FakeGenaiClient(response=FakeGenaiResponse("interview answer"))
        provider: LLMProvider = GeminiProvider(client=fake_client)

        response = provider.generate("What is your experience?")
        assert response == "interview answer"

    def test_abstract_class_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            LLMProvider()  # type: ignore[abstract]


class TestDotenvLoading:
    """Tests for the .env configuration loader."""

    def test_load_env_from_explicit_file(self, tmp_path, monkeypatch) -> None:
        from app.llm.config import load_env

        env_file = tmp_path / ".env"
        env_file.write_text("GEMINI_API_KEY=test-fake-key\n", encoding="utf-8")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        load_env(env_file)

        assert os.getenv("GEMINI_API_KEY") == "test-fake-key"

    def test_load_env_missing_file_does_nothing(self, tmp_path, monkeypatch) -> None:
        from app.llm.config import load_env

        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        missing = tmp_path / "does-not-exist.env"

        load_env(missing)  # should not raise

        assert os.getenv("GEMINI_API_KEY") is None