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
        monkeypatch.setenv("OPENROUTER_API_KEY_1", "test-key-123")
        monkeypatch.setenv("OPENROUTER_MODEL_1", DEFAULT_OPENROUTER_MODEL)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
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
        monkeypatch.setenv("OPENROUTER_API_KEY_1", "key1")
        monkeypatch.setenv("OPENROUTER_MODEL_1", "openrouter/auto")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
        client = FakeHTTPClient(response=_openrouter_response("ok"))
        provider = OpenRouterProvider(client=client)

        provider.generate("hi")

        assert client.last_json["model"] == "openrouter/auto"


class TestMissingConfiguration:
    """Tests for missing API configuration."""

    def test_missing_api_key_raises_configuration_error(self, monkeypatch) -> None:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
        for idx in range(1, 10):
            monkeypatch.delenv(f"OPENROUTER_API_KEY_{idx}", raising=False)
            monkeypatch.delenv(f"OPENROUTER_MODEL_{idx}", raising=False)
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


class TestFailover:
    """Tests for multi-key/model failover behavior."""

    def test_one_configured_pair_succeeds(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY_1", "key1")
        monkeypatch.setenv("OPENROUTER_MODEL_1", "model1")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
        client = FakeHTTPClient(response=_openrouter_response("ok"))
        provider = OpenRouterProvider(client=client)

        result = provider.generate("hi")

        assert result == "ok"
        assert provider.generate_count == 1

    def test_429_then_success_fails_over(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY_1", "key1")
        monkeypatch.setenv("OPENROUTER_MODEL_1", "model1")
        monkeypatch.setenv("OPENROUTER_API_KEY_2", "key2")
        monkeypatch.setenv("OPENROUTER_MODEL_2", "model2")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

        first_client = FakeHTTPClient(response=FakeResponse(status_code=429, json_data={}))
        second_client = FakeHTTPClient(response=_openrouter_response("recovered"))

        class MultiClient:
            def __init__(self) -> None:
                self.calls = 0
            def post(self, *args, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    return first_client.post(*args, **kwargs)
                return second_client.post(*args, **kwargs)

        provider = OpenRouterProvider(client=MultiClient())
        result = provider.generate("hi")

        assert result == "recovered"
        assert provider.generate_count == 1

    def test_500_then_success_fails_over(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY_1", "key1")
        monkeypatch.setenv("OPENROUTER_MODEL_1", "model1")
        monkeypatch.setenv("OPENROUTER_API_KEY_2", "key2")
        monkeypatch.setenv("OPENROUTER_MODEL_2", "model2")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

        first_client = FakeHTTPClient(response=FakeResponse(status_code=500, json_data={}))
        second_client = FakeHTTPClient(response=_openrouter_response("recovered"))

        class MultiClient:
            def __init__(self) -> None:
                self.calls = 0
            def post(self, *args, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    return first_client.post(*args, **kwargs)
                return second_client.post(*args, **kwargs)

        provider = OpenRouterProvider(client=MultiClient())
        result = provider.generate("hi")

        assert result == "recovered"

    def test_timeout_then_success_fails_over(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY_1", "key1")
        monkeypatch.setenv("OPENROUTER_MODEL_1", "model1")
        monkeypatch.setenv("OPENROUTER_API_KEY_2", "key2")
        monkeypatch.setenv("OPENROUTER_MODEL_2", "model2")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

        first_client = FakeHTTPClient(error=TimeoutError("timed out"))
        second_client = FakeHTTPClient(response=_openrouter_response("recovered"))

        class MultiClient:
            def __init__(self) -> None:
                self.calls = 0
            def post(self, *args, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    return first_client.post(*args, **kwargs)
                return second_client.post(*args, **kwargs)

        provider = OpenRouterProvider(client=MultiClient())
        result = provider.generate("hi")

        assert result == "recovered"

    def test_all_keys_fail_raises(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY_1", "key1")
        monkeypatch.setenv("OPENROUTER_MODEL_1", "model1")
        monkeypatch.setenv("OPENROUTER_API_KEY_2", "key2")
        monkeypatch.setenv("OPENROUTER_MODEL_2", "model2")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

        client = FakeHTTPClient(error=ConnectionError("connection reset"))

        provider = OpenRouterProvider(client=client)

        with pytest.raises(LLMGenerationError):
            provider.generate("hi")

    def test_correct_model_used_with_each_key(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY_1", "key1")
        monkeypatch.setenv("OPENROUTER_MODEL_1", "model-a")
        monkeypatch.setenv("OPENROUTER_API_KEY_2", "key2")
        monkeypatch.setenv("OPENROUTER_MODEL_2", "model-b")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

        first_client = FakeHTTPClient(response=FakeResponse(status_code=500, json_data={}))
        second_client = FakeHTTPClient(response=_openrouter_response("ok"))

        class MultiClient:
            def __init__(self) -> None:
                self.calls = 0
            def post(self, url, *, headers, json):
                self.calls += 1
                if self.calls == 1:
                    return first_client.post(url, headers=headers, json=json)
                return second_client.post(url, headers=headers, json=json)

        provider = OpenRouterProvider(client=MultiClient())
        provider.generate("hi")

        assert first_client.last_json["model"] == "model-a"
        assert second_client.last_json["model"] == "model-b"

    def test_legacy_single_key_still_works(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "legacy-key")
        monkeypatch.setenv("OPENROUTER_MODEL", "legacy-model")
        monkeypatch.delenv("OPENROUTER_API_KEY_1", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL_1", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY_2", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL_2", raising=False)

        client = FakeHTTPClient(response=_openrouter_response("legacy-ok"))
        provider = OpenRouterProvider(client=client)

        result = provider.generate("hi")

        assert result == "legacy-ok"
        assert client.last_json["model"] == "legacy-model"

    def test_missing_numbered_config_does_not_crash(self, monkeypatch) -> None:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY_1", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL_1", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY_2", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL_2", raising=False)

        provider = OpenRouterProvider(client=FakeHTTPClient(response=_openrouter_response("x")))

        assert provider._pairs == [("injected-client", DEFAULT_OPENROUTER_MODEL)]

        # Backward compatibility: injected client allows generation without
        # environment configuration (used by existing tests).
        result = provider.generate("hi")
        assert result == "x"

    def test_api_keys_never_in_exception_messages(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY_1", "secret-key-1")
        monkeypatch.setenv("OPENROUTER_MODEL_1", "model1")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

        client = FakeHTTPClient(error=RuntimeError("boom"))

        provider = OpenRouterProvider(client=client)

        with pytest.raises(LLMGenerationError) as excinfo:
            provider.generate("hi")

        message = str(excinfo.value)
        assert "secret-key-1" not in message
        assert "Bearer" not in message

    def test_timing_instrumentation_preserved(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY_1", "key1")
        monkeypatch.setenv("OPENROUTER_MODEL_1", "model1")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

        client = FakeHTTPClient(response=_openrouter_response("ok"))
        provider = OpenRouterProvider(client=client)

        provider.generate("hi")

        assert provider.generate_count == 1
        assert provider.last_generate_elapsed_s is not None
        assert provider.last_generate_elapsed_s >= 0

    def test_first_two_fail_third_succeeds(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY_1", "key1")
        monkeypatch.setenv("OPENROUTER_MODEL_1", "model1")
        monkeypatch.setenv("OPENROUTER_API_KEY_2", "key2")
        monkeypatch.setenv("OPENROUTER_MODEL_2", "model2")
        monkeypatch.setenv("OPENROUTER_API_KEY_3", "key3")
        monkeypatch.setenv("OPENROUTER_MODEL_3", "model3")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

        first_client = FakeHTTPClient(response=FakeResponse(status_code=500, json_data={}))
        second_client = FakeHTTPClient(response=FakeResponse(status_code=429, json_data={}))
        third_client = FakeHTTPClient(response=_openrouter_response("recovered"))

        class MultiClient:
            def __init__(self) -> None:
                self.calls = 0
            def post(self, url, *, headers, json):
                self.calls += 1
                if self.calls == 1:
                    return first_client.post(url, headers=headers, json=json)
                if self.calls == 2:
                    return second_client.post(url, headers=headers, json=json)
                return third_client.post(url, headers=headers, json=json)

        provider = OpenRouterProvider(client=MultiClient())
        result = provider.generate("hi")

        assert result == "recovered"

    def test_missing_model_defaults_to_free(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY_1", "key1")
        monkeypatch.delenv("OPENROUTER_MODEL_1", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

        client = FakeHTTPClient(response=_openrouter_response("ok"))
        provider = OpenRouterProvider(client=client)

        provider.generate("hi")

        assert client.last_json["model"] == DEFAULT_OPENROUTER_MODEL

    def test_correct_key_model_pairs_used(self, monkeypatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY_1", "key1")
        monkeypatch.setenv("OPENROUTER_MODEL_1", "model-a")
        monkeypatch.setenv("OPENROUTER_API_KEY_2", "key2")
        monkeypatch.setenv("OPENROUTER_MODEL_2", "model-b")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

        first_client = FakeHTTPClient(response=FakeResponse(status_code=500, json_data={}))
        second_client = FakeHTTPClient(response=_openrouter_response("ok"))

        class MultiClient:
            def __init__(self) -> None:
                self.calls = 0
            def post(self, url, *, headers, json):
                self.calls += 1
                if self.calls == 1:
                    return first_client.post(url, headers=headers, json=json)
                return second_client.post(url, headers=headers, json=json)

        provider = OpenRouterProvider(client=MultiClient())
        provider.generate("hi")

        assert first_client.last_json["model"] == "model-a"
        assert second_client.last_json["model"] == "model-b"
