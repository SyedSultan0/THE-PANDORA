"""Tests for the OpenRouter LLM provider.

No real network calls or API keys are used — the provider is exercised with a
mock HTTP client.
"""

import pytest

from app.llm import (
    LLMConfigurationError,
    LLMError,
    LLMGenerationError,
    LLMProvider,
    OpenRouterProvider,
)
from app.llm.openrouter import DEFAULT_OPENROUTER_MODEL, OPENROUTER_ENDPOINT


class FakeResponse:
    """Minimal stand-in for ``httpx.Response``."""

    def __init__(self, status_code: int = 200, json_data=None) -> None:
        self.status_code = status_code
        self._json_data = json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise _FakeHTTPStatusError(f"HTTP {self.status_code} error")

    def json(self):
        return self._json_data


class _FakeHTTPStatusError(Exception):
    """Stand-in resembling httpx.HTTPStatusError."""


class FakeHTTPClient:
    """Stand-in for ``httpx.Client`` recording the last request."""

    def __init__(self, response: FakeResponse | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.last_url: str | None = None
        self.last_headers: dict | None = None
        self.last_json: dict | None = None

    def post(self, url: str, *, headers: dict, json: dict) -> FakeResponse:
        self.last_url = url
        self.last_headers = headers
        self.last_json = json
        if self.error is not None:
            raise self.error
        return self.response


def _openrouter_response(text: str = "Hello, world!") -> FakeResponse:
    return FakeResponse(
        status_code=200,
        json_data={"choices": [{"message": {"content": text}}]},
    )


class TestGenerateSuccess:
    """Tests for successful text generation."""

    def test_returns_generated_text(self) -> None:
        client = FakeHTTPClient(response=_openrouter_response("Hello from OpenRouter!"))
        provider = OpenRouterProvider(client=client)

        result = provider.generate("Say hello")

        assert result == "Hello from OpenRouter!"

    def test_uses_openrouter_endpoint(self) -> None:
        client = FakeHTTPClient(response=_openrouter_response("ok"))
        provider = OpenRouterProvider(client=client)

        provider.generate("hi")

        assert client.last_url == OPENROUTER_ENDPOINT

    def test_sends_bearer_auth_header(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-123")
        client = FakeHTTPClient(response=_openrouter_response("ok"))
        provider = OpenRouterProvider(client=client)

        provider.generate("hi")

        assert client.last_headers["Authorization"] == "Bearer test-key-123"
        assert client.last_headers["Content-Type"] == "application/json"

    def test_sends_prompt_as_user_message(self) -> None:
        client = FakeHTTPClient(response=_openrouter_response("ok"))
        provider = OpenRouterProvider(client=client)

        provider.generate("Tell me about embeddings.")

        assert client.last_json["messages"] == [
            {"role": "user", "content": "Tell me about embeddings."}
        ]

    def test_uses_default_model_when_env_not_set(self, monkeypatch) -> None:
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
        client = FakeHTTPClient(response=_openrouter_response("ok"))
        provider = OpenRouterProvider(client=client)

        provider.generate("hi")

        assert provider._model == DEFAULT_OPENROUTER_MODEL
        assert client.last_json["model"] == DEFAULT_OPENROUTER_MODEL

    def test_uses_model_from_environment(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/auto")
        client = FakeHTTPClient(response=_openrouter_response("ok"))
        provider = OpenRouterProvider(client=client)

        provider.generate("hi")

        assert client.last_json["model"] == "openrouter/auto"


class TestMissingConfiguration:
    """Tests for missing API configuration."""

    def test_missing_api_key_raises_configuration_error(self, monkeypatch) -> None:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        provider = OpenRouterProvider()  # no client injected

        with pytest.raises(LLMConfigurationError) as excinfo:
            provider.generate("hello")

        assert "OPENROUTER_API_KEY" in str(excinfo.value)

    def test_configuration_error_is_llm_error(self, monkeypatch) -> None:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        provider = OpenRouterProvider()

        with pytest.raises(LLMError):
            provider.generate("hello")

    def test_injected_client_bypasses_api_key_check(self, monkeypatch) -> None:
        """With an injected client, no API key is required (used in tests)."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        client = FakeHTTPClient(response=_openrouter_response("ok"))
        provider = OpenRouterProvider(client=client)

        result = provider.generate("hi")

        assert result == "ok"


class TestProviderFailure:
    """Tests for provider/API error handling."""

    def test_http_error_wrapped_in_generation_error(self) -> None:
        client = FakeHTTPClient(response=FakeResponse(status_code=500, json_data={}))
        provider = OpenRouterProvider(client=client)

        with pytest.raises(LLMGenerationError) as excinfo:
            provider.generate("hello")

        assert "OpenRouter" in str(excinfo.value)

    def test_generation_error_is_llm_error(self) -> None:
        client = FakeHTTPClient(response=FakeResponse(status_code=502, json_data={}))
        provider = OpenRouterProvider(client=client)

        with pytest.raises(LLMError):
            provider.generate("hello")

    def test_network_error_wrapped_in_generation_error(self) -> None:
        client = FakeHTTPClient(error=ConnectionError("connection reset"))
        provider = OpenRouterProvider(client=client)

        with pytest.raises(LLMGenerationError) as excinfo:
            provider.generate("hello")

        assert "connection reset" in str(excinfo.value)

    def test_raw_http_exception_does_not_leak(self) -> None:
        client = FakeHTTPClient(error=RuntimeError("raw network error"))
        provider = OpenRouterProvider(client=client)

        with pytest.raises(LLMGenerationError):
            provider.generate("hello")
        # The raw exception must not escape as its original type.
        with pytest.raises(Exception) as excinfo:
            provider.generate("hello")
        assert not isinstance(excinfo.value, RuntimeError)

    def test_missing_choices_field_raises_generation_error(self) -> None:
        client = FakeHTTPClient(response=FakeResponse(status_code=200, json_data={}))
        provider = OpenRouterProvider(client=client)

        with pytest.raises(LLMGenerationError):
            provider.generate("hello")

    def test_empty_content_raises_generation_error(self) -> None:
        client = FakeHTTPClient(response=_openrouter_response(""))
        provider = OpenRouterProvider(client=client)

        with pytest.raises(LLMGenerationError, match="empty response"):
            provider.generate("hello")

    def test_non_string_content_raises_generation_error(self) -> None:
        client = FakeHTTPClient(response=_openrouter_response(""))
        client.response._json_data = {"choices": [{"message": {"content": 123}}]}
        provider = OpenRouterProvider(client=client)

        with pytest.raises(LLMGenerationError, match="empty response"):
            provider.generate("hello")


class TestAbstraction:
    """Tests that the abstraction hides provider specifics."""

    def test_openrouter_provider_is_an_llm_provider(self) -> None:
        provider = OpenRouterProvider(client=FakeHTTPClient(response=_openrouter_response("x")))
        assert isinstance(provider, LLMProvider)

    def test_usage_through_interface_only(self) -> None:
        client = FakeHTTPClient(response=_openrouter_response("interview answer"))
        provider: LLMProvider = OpenRouterProvider(client=client)

        response = provider.generate("What is your experience?")
        assert response == "interview answer"