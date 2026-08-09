"""Tests for the QuestionGenerator and its prompt builder.

No real Gemini/API calls are made — a fake LLMProvider is used.
"""

import json

import pytest

from app.context import build_interview_context
from app.context.models import InterviewState
from app.interview import (
    GeneratedQuestion,
    QuestionGenerator,
    build_question_prompt,
)
from app.interview.errors import QuestionValidationError
from app.interview.prompts import (
    QUESTION_OUTPUT_INSTRUCTIONS,
    QUESTION_SYSTEM_PROMPT,
)
from app.loaders.candidates import load_candidates
from app.loaders.curriculum import load_curriculum
from app.llm import LLMError, LLMGenerationError, LLMProvider


class FakeLLMProvider(LLMProvider):
    """A scriptable fake provider implementing the LLMProvider interface."""

    def __init__(self, response: str | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def _valid_question_json(**overrides) -> str:
    payload = {
        "question": "Explain how vector embeddings are generated.",
        "curriculum_day": 7,
        "topic": "Embeddings",
        "difficulty": "medium",
    }
    payload.update(overrides)
    return json.dumps(payload)


@pytest.fixture(scope="module")
def real_context():
    """A real InterviewContext built from the actual organizer data."""
    candidate = load_candidates().candidates[0]  # CAND-001 Sarah Johnson
    curriculum = load_curriculum()
    return build_interview_context(candidate, curriculum)


class TestInteractsWithGenericProvider:
    """Tests that QuestionGenerator uses the generic LLMProvider interface."""

    def test_accepts_any_llm_provider(self, real_context) -> None:
        fake = FakeLLMProvider(response=_valid_question_json())
        generator = QuestionGenerator(fake)

        assert isinstance(generator._llm, LLMProvider)

    def test_generates_question(self, real_context) -> None:
        fake = FakeLLMProvider(response=_valid_question_json())
        generator = QuestionGenerator(fake)

        result = generator.generate(real_context)

        assert isinstance(result, GeneratedQuestion)
        assert result.question == "Explain how vector embeddings are generated."
        assert result.curriculum_day == 7
        assert result.topic == "Embeddings"
        assert result.difficulty == "medium"

    def test_uses_provider_generate(self, real_context) -> None:
        fake = FakeLLMProvider(response=_valid_question_json())
        generator = QuestionGenerator(fake)

        generator.generate(real_context)

        assert fake.last_prompt is not None


class TestPromptContent:
    """Tests for how InterviewContext is converted into the prompt."""

    def test_prompt_includes_candidate_information(self, real_context) -> None:
        fake = FakeLLMProvider(response=_valid_question_json())
        QuestionGenerator(fake).generate(real_context)

        prompt = fake.last_prompt
        assert "Senior Data Engineer" in prompt
        assert "9" in prompt
        assert "MS Computer Science" in prompt

    def test_prompt_includes_mission_history(self, real_context) -> None:
        fake = FakeLLMProvider(response=_valid_question_json())
        QuestionGenerator(fake).generate(real_context)

        prompt = fake.last_prompt
        assert "Embeddings Explained" in prompt
        assert "PASSED" in prompt
        assert "SKIPPED" in prompt

    def test_prompt_includes_curriculum_days(self, real_context) -> None:
        fake = FakeLLMProvider(response=_valid_question_json())
        QuestionGenerator(fake).generate(real_context)

        prompt = fake.last_prompt
        assert "Day 7" in prompt
        assert "Embeddings Explained" in prompt

    def test_prompt_includes_difficulty_when_supplied(self, real_context) -> None:
        state = InterviewState(currentDifficulty="hard")
        ctx = real_context.model_copy(update={"interviewState": state})
        fake = FakeLLMProvider(response=_valid_question_json())
        QuestionGenerator(fake).generate(ctx)

        prompt = fake.last_prompt
        assert "Current difficulty: hard" in prompt

    def test_prompt_includes_previously_asked_questions(self, real_context) -> None:
        state = InterviewState(questionsAsked=["What is a vector?"])
        ctx = real_context.model_copy(update={"interviewState": state})
        fake = FakeLLMProvider(response=_valid_question_json())
        QuestionGenerator(fake).generate(ctx)

        prompt = fake.last_prompt
        assert "What is a vector?" in prompt

    def test_prompt_includes_covered_days(self, real_context) -> None:
        state = InterviewState(daysCovered=[7])
        ctx = real_context.model_copy(update={"interviewState": state})
        fake = FakeLLMProvider(response=_valid_question_json())
        QuestionGenerator(fake).generate(ctx)

        prompt = fake.last_prompt
        # The prompt uses a human-readable label; the covered day must appear.
        assert "Days already covered: [7]" in prompt

    def test_prompt_contains_system_instructions(self, real_context) -> None:
        prompt = build_question_prompt(real_context)
        assert QUESTION_SYSTEM_PROMPT in prompt
        assert QUESTION_OUTPUT_INSTRUCTIONS in prompt

    def test_prompt_does_not_dump_raw_json(self, real_context) -> None:
        prompt = build_question_prompt(real_context)
        # The prompt is a normalized summary; raw candidate JSON blobs are not dumped.
        assert '"member"' not in prompt
        assert '"missions"' not in prompt


class TestStructureSafeParsing:
    """Tests for structured-output parsing (markdown fences, etc.)."""

    def test_accepts_fenced_json(self, real_context) -> None:
        raw = "```json\n" + _valid_question_json() + "\n```"
        fake = FakeLLMProvider(response=raw)
        result = QuestionGenerator(fake).generate(real_context)

        assert result.question == "Explain how vector embeddings are generated."

    def test_accepts_null_metadata(self, real_context) -> None:
        raw = json.dumps(
            {"question": "Tell me about yourself.", "curriculum_day": None,
             "topic": None, "difficulty": None}
        )
        fake = FakeLLMProvider(response=raw)
        result = QuestionGenerator(fake).generate(real_context)

        assert result.question == "Tell me about yourself."
        assert result.curriculum_day is None
        assert result.topic is None
        assert result.difficulty is None


class TestValidationFailures:
    """Tests for invalid LLM output handling."""

    def test_empty_output_rejected(self, real_context) -> None:
        fake = FakeLLMProvider(response="")
        with pytest.raises(QuestionValidationError, match="empty response"):
            QuestionGenerator(fake).generate(real_context)

    def test_whitespace_output_rejected(self, real_context) -> None:
        fake = FakeLLMProvider(response="   \n  ")
        with pytest.raises(QuestionValidationError, match="empty response"):
            QuestionGenerator(fake).generate(real_context)

    def test_non_json_output_rejected(self, real_context) -> None:
        fake = FakeLLMProvider(response="not json at all")
        with pytest.raises(QuestionValidationError, match="not valid JSON"):
            QuestionGenerator(fake).generate(real_context)

    def test_non_object_json_rejected(self, real_context) -> None:
        fake = FakeLLMProvider(response="[1, 2, 3]")
        with pytest.raises(QuestionValidationError, match="must be a JSON object"):
            QuestionGenerator(fake).generate(real_context)

    def test_missing_question_rejected(self, real_context) -> None:
        fake = FakeLLMProvider(response=json.dumps({"topic": "x"}))
        with pytest.raises(QuestionValidationError, match="'question'"):
            QuestionGenerator(fake).generate(real_context)

    def test_empty_question_rejected(self, real_context) -> None:
        fake = FakeLLMProvider(response=json.dumps({"question": "   "}))
        with pytest.raises(QuestionValidationError, match="'question'"):
            QuestionGenerator(fake).generate(real_context)

    def test_invalid_curriculum_day_rejected(self, real_context) -> None:
        """A curriculum_day not in the context is rejected."""
        raw = _valid_question_json(curriculum_day=999)
        fake = FakeLLMProvider(response=raw)
        with pytest.raises(QuestionValidationError, match="not in the supplied context"):
            QuestionGenerator(fake).generate(real_context)

    def test_curriculum_day_must_be_int(self, real_context) -> None:
        raw = _valid_question_json(curriculum_day="7")
        fake = FakeLLMProvider(response=raw)
        with pytest.raises(QuestionValidationError, match="'curriculum_day' must be an integer"):
            QuestionGenerator(fake).generate(real_context)

    def test_topic_must_be_str(self, real_context) -> None:
        raw = _valid_question_json(topic=123)
        fake = FakeLLMProvider(response=raw)
        with pytest.raises(QuestionValidationError, match="'topic' must be a string"):
            QuestionGenerator(fake).generate(real_context)

    def test_difficulty_must_be_str(self, real_context) -> None:
        raw = _valid_question_json(difficulty=5)
        fake = FakeLLMProvider(response=raw)
        with pytest.raises(QuestionValidationError, match="'difficulty' must be a string"):
            QuestionGenerator(fake).generate(real_context)


class FakeLLMProviderWithQueue(LLMProvider):
    """Fake provider that returns queued responses in order."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.call_count = 0
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        if not self.responses:
            raise AssertionError("No more queued responses.")
        self.call_count += 1
        return self.responses.pop(0)


class TestRetryBehavior:
    """Tests for the bounded retry/recovery logic in generate_json."""

    def test_retry_succeeds_on_second_attempt(self, real_context) -> None:
        fake = FakeLLMProviderWithQueue(
            responses=["plain text with no json here", '{"question":"Q","curriculum_day":7,"topic":"T","difficulty":"medium"}']
        )
        turn = QuestionGenerator(fake).generate(real_context)
        assert turn.question == "Q"
        assert fake.call_count == 2

    def test_retry_exhausted_raises(self, real_context) -> None:
        fake = FakeLLMProviderWithQueue(responses=["not json", "still not json"])
        with pytest.raises(QuestionValidationError, match="Expecting value"):
            QuestionGenerator(fake).generate(real_context)
        assert fake.call_count == 2

    def test_fenced_json_is_accepted(self, real_context) -> None:
        fake = FakeLLMProviderWithQueue(
            responses=['```json\n{"question":"Q","curriculum_day":7,"topic":"T","difficulty":"medium"}\n```']
        )
        turn = QuestionGenerator(fake).generate(real_context)
        assert turn.question == "Q"

    def test_whitespace_around_json_is_accepted(self, real_context) -> None:
        fake = FakeLLMProviderWithQueue(
            responses=['  \n\n{"question":"Q","curriculum_day":7,"topic":"T","difficulty":"medium"}  \n']
        )
        turn = QuestionGenerator(fake).generate(real_context)
        assert turn.question == "Q"

    def test_malformed_json_retried(self, real_context) -> None:
        fake = FakeLLMProviderWithQueue(
            responses=['{"question":"Q"', '{"question":"Q","curriculum_day":7,"topic":"T","difficulty":"medium"}']
        )
        turn = QuestionGenerator(fake).generate(real_context)
        assert turn.question == "Q"
        assert fake.call_count == 2


class TestProviderErrors:
    """Tests that provider errors propagate cleanly."""

    def test_provider_error_propagates(self, real_context) -> None:
        fake = FakeLLMProvider(error=LLMGenerationError("API unavailable"))
        with pytest.raises(LLMError):
            QuestionGenerator(fake).generate(real_context)

    def test_question_generator_does_not_require_gemini(self) -> None:
        """The generator depends on LLMProvider, never on GeminiProvider."""
        import inspect

        source = inspect.getsource(QuestionGenerator)
        assert "GeminiProvider" not in source
        assert "google" not in source