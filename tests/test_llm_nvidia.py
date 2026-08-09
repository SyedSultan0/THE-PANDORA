"""Tests for the NVIDIA LLM provider.

No real network calls or API keys are used — the provider is exercised with a
mock HTTP client.
"""

import pytest

from app.llm import (
    LLMConfigurationError,
    LLMError,
    LLMGenerationError,
    LLMProvider,
    NvidiaProvider,
)
from app.llm.nvidia import DEFAULT_NVIDIA_MODEL, NVIDIA_ENDPOINT


class FakeResponse:
    """Minimal stand-in for ``httpx.Response``."""

    def __init__(self, status_code: int = 200, json_data=None) -> None:
        self.status_code = status_code
        self._json_data = json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise _FakeHTTPStatusError(f"HTTP {self.status_code} error", status_code=self.status_code)

    def json(self):
        return self._json_data


class _FakeHTTPStatusError(Exception):
    """Stand-in resembling httpx.HTTPStatusError."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


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


def _nvidia_response(text: str = "Hello, world!") -> FakeResponse:
    return FakeResponse(
        status_code=200,
        json_data={"choices": [{"message": {"content": text}}]},
    )


class TestGenerateSuccess:
    """Tests for successful text generation."""

    def test_returns_generated_text(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        client = FakeHTTPClient(response=_nvidia_response("Hello from NVIDIA!"))
        provider = NvidiaProvider(client=client)

        result = provider.generate("Say hello")

        assert result == "Hello from NVIDIA!"

    def test_uses_nvidia_endpoint(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        client = FakeHTTPClient(response=_nvidia_response("ok"))
        provider = NvidiaProvider(client=client)

        provider.generate("hi")

        assert client.last_url == NVIDIA_ENDPOINT

    def test_sends_bearer_auth_header(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key-123")
        client = FakeHTTPClient(response=_nvidia_response("ok"))
        provider = NvidiaProvider(client=client)

        provider.generate("hi")

        assert client.last_headers["Authorization"] == "Bearer test-key-123"
        assert client.last_headers["Content-Type"] == "application/json"

    def test_sends_prompt_as_user_message(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        client = FakeHTTPClient(response=_nvidia_response("ok"))
        provider = NvidiaProvider(client=client)

        provider.generate("Tell me about embeddings.")

        assert client.last_json["messages"] == [
            {"role": "user", "content": "Tell me about embeddings."}
        ]

    def test_uses_default_model_when_env_not_set(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        monkeypatch.delenv("NVIDIA_MODEL", raising=False)
        client = FakeHTTPClient(response=_nvidia_response("ok"))
        provider = NvidiaProvider(client=client)

        provider.generate("hi")

        assert provider._model == DEFAULT_NVIDIA_MODEL
        assert client.last_json["model"] == DEFAULT_NVIDIA_MODEL

    def test_uses_model_from_environment(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        monkeypatch.setenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
        client = FakeHTTPClient(response=_nvidia_response("ok"))
        provider = NvidiaProvider(client=client)

        provider.generate("hi")

        assert client.last_json["model"] == "meta/llama-3.1-8b-instruct"


class TestMissingConfiguration:
    """Tests for missing API configuration."""

    def test_missing_api_key_raises_configuration_error(self, monkeypatch) -> None:
        monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
        provider = NvidiaProvider()  # no client injected

        with pytest.raises(LLMConfigurationError) as excinfo:
            provider.generate("hello")

        assert "NVIDIA_API_KEY" in str(excinfo.value)

    def test_configuration_error_is_llm_error(self, monkeypatch) -> None:
        monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
        provider = NvidiaProvider()

        with pytest.raises(LLMError):
            provider.generate("hello")


class TestProviderFailure:
    """Tests for provider/API error handling."""

    def test_http_429_wrapped_in_generation_error(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        client = FakeHTTPClient(response=FakeResponse(status_code=429, json_data={}))
        provider = NvidiaProvider(client=client)

        with pytest.raises(LLMGenerationError) as excinfo:
            provider.generate("hello")

        assert "NVIDIA" in str(excinfo.value)

    def test_http_500_wrapped_in_generation_error(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        client = FakeHTTPClient(response=FakeResponse(status_code=500, json_data={}))
        provider = NvidiaProvider(client=client)

        with pytest.raises(LLMGenerationError) as excinfo:
            provider.generate("hello")

        assert "NVIDIA" in str(excinfo.value)

    def test_timeout_wrapped_in_generation_error(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        client = FakeHTTPClient(error=TimeoutError("timed out"))
        provider = NvidiaProvider(client=client)

        with pytest.raises(LLMGenerationError) as excinfo:
            provider.generate("hello")

        assert "timed out" in str(excinfo.value)

    def test_connection_error_wrapped_in_generation_error(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        client = FakeHTTPClient(error=ConnectionError("connection reset"))
        provider = NvidiaProvider(client=client)

        with pytest.raises(LLMGenerationError) as excinfo:
            provider.generate("hello")

        assert "connection reset" in str(excinfo.value)

    def test_malformed_json_raises_generation_error(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        client = FakeHTTPClient(response=FakeResponse(status_code=200, json_data="not json"))
        provider = NvidiaProvider(client=client)

        with pytest.raises(LLMGenerationError):
            provider.generate("hello")

    def test_missing_choices_field_raises_generation_error(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        client = FakeHTTPClient(response=FakeResponse(status_code=200, json_data={}))
        provider = NvidiaProvider(client=client)

        with pytest.raises(LLMGenerationError):
            provider.generate("hello")

    def test_empty_content_raises_generation_error(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        client = FakeHTTPClient(response=_nvidia_response(""))
        provider = NvidiaProvider(client=client)

        with pytest.raises(LLMGenerationError, match="empty response"):
            provider.generate("hello")

    def test_api_key_never_in_exception_messages(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "secret-nvidia-key")
        client = FakeHTTPClient(error=RuntimeError("boom"))
        provider = NvidiaProvider(client=client)

        with pytest.raises(LLMGenerationError) as excinfo:
            provider.generate("hello")

        message = str(excinfo.value)
        assert "secret-nvidia-key" not in message
        assert "Bearer" not in message


class TestAbstraction:
    """Tests that the abstraction hides provider specifics."""

    def test_nvidia_provider_is_an_llm_provider(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        provider = NvidiaProvider(client=FakeHTTPClient(response=_nvidia_response("x")))
        assert isinstance(provider, LLMProvider)

    def test_usage_through_interface_only(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        client = FakeHTTPClient(response=_nvidia_response("interview answer"))
        provider: LLMProvider = NvidiaProvider(client=client)

        response = provider.generate("What is your experience?")
        assert response == "interview answer"

    def test_timing_instrumentation_preserved(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        client = FakeHTTPClient(response=_nvidia_response("ok"))
        provider = NvidiaProvider(client=client)

        provider.generate("hi")

        assert provider.generate_count == 1
        assert provider.last_generate_elapsed_s is not None
        assert provider.last_generate_elapsed_s >= 0