"""Tests for the FollowUpGenerator and its prompt builder.

No real Gemini/API calls are made — a fake LLMProvider is used.
"""

import json

import pytest

from app.context import build_interview_context
from app.context.models import InterviewState
from app.interview import (
    EvaluationResult,
    FollowUpGenerator,
    GeneratedQuestion,
    build_follow_up_prompt,
)
from app.interview.errors import QuestionValidationError
from app.interview.prompts import (
    FOLLOW_UP_OUTPUT_INSTRUCTIONS,
    FOLLOW_UP_SYSTEM_PROMPT,
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


def _valid_follow_up_json(**overrides) -> str:
    payload = {
        "question": "Can you explain how you would handle the edge case you mentioned?",
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


@pytest.fixture(scope="module")
def original_question():
    return GeneratedQuestion(
        question="Explain how vector embeddings are generated.",
        curriculum_day=7,
        topic="Embeddings",
        difficulty="medium",
    )


@pytest.fixture(scope="module")
def evaluation():
    return EvaluationResult(
        score=5,
        correctness="PARTIAL",
        strengths=["Mentioned the basic idea"],
        gaps=["Did not explain the training process"],
        reasoning="Partial understanding shown.",
        confidence="MEDIUM",
    )


class TestGeneratorInteractsWithGenericProvider:
    """Tests that FollowUpGenerator uses the generic LLMProvider interface."""

    def test_accepts_any_llm_provider(self, real_context, original_question, evaluation) -> None:
        fake = FakeLLMProvider(response=_valid_follow_up_json())
        generator = FollowUpGenerator(fake)

        assert isinstance(generator._llm, LLMProvider)

    def test_valid_input_produces_follow_up(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(response=_valid_follow_up_json())
        generator = FollowUpGenerator(fake)

        result = generator.generate(
            original_question, "My answer.", evaluation, real_context
        )

        assert isinstance(result, GeneratedQuestion)
        assert result.question == "Can you explain how you would handle the edge case you mentioned?"
        assert result.curriculum_day == 7
        assert result.topic == "Embeddings"
        assert result.difficulty == "medium"

    def test_uses_provider_generate(self, real_context, original_question, evaluation) -> None:
        fake = FakeLLMProvider(response=_valid_follow_up_json())
        generator = FollowUpGenerator(fake)

        generator.generate(original_question, "My answer.", evaluation, real_context)

        assert fake.last_prompt is not None


class TestPromptContent:
    """Tests for how question/answer/evaluation/context appear in the prompt."""

    def test_prompt_includes_original_question(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(response=_valid_follow_up_json())
        FollowUpGenerator(fake).generate(
            original_question, "Answer.", evaluation, real_context
        )

        prompt = fake.last_prompt
        assert "Explain how vector embeddings are generated." in prompt

    def test_prompt_includes_candidate_answer(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(response=_valid_follow_up_json())
        FollowUpGenerator(fake).generate(
            original_question, "I said something specific.", evaluation, real_context
        )

        prompt = fake.last_prompt
        assert "I said something specific." in prompt

    def test_prompt_includes_evaluation_score(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(response=_valid_follow_up_json())
        FollowUpGenerator(fake).generate(
            original_question, "Answer.", evaluation, real_context
        )

        prompt = fake.last_prompt
        assert "Score: 5/10" in prompt

    def test_prompt_includes_evaluation_correctness(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(response=_valid_follow_up_json())
        FollowUpGenerator(fake).generate(
            original_question, "Answer.", evaluation, real_context
        )

        prompt = fake.last_prompt
        assert "Correctness: PARTIAL" in prompt

    def test_prompt_includes_evaluation_gaps(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(response=_valid_follow_up_json())
        FollowUpGenerator(fake).generate(
            original_question, "Answer.", evaluation, real_context
        )

        prompt = fake.last_prompt
        assert "Did not explain the training process" in prompt

    def test_prompt_includes_candidate_context(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(response=_valid_follow_up_json())
        FollowUpGenerator(fake).generate(
            original_question, "Answer.", evaluation, real_context
        )

        prompt = fake.last_prompt
        assert "Senior Data Engineer" in prompt

    def test_prompt_includes_current_difficulty(
        self, real_context, original_question, evaluation
    ) -> None:
        state = InterviewState(currentDifficulty="hard")
        ctx = real_context.model_copy(update={"interviewState": state})
        fake = FakeLLMProvider(response=_valid_follow_up_json())
        FollowUpGenerator(fake).generate(original_question, "Answer.", evaluation, ctx)

        prompt = fake.last_prompt
        assert "Current difficulty: hard" in prompt

    def test_prompt_contains_system_instructions(
        self, real_context, original_question, evaluation
    ) -> None:
        prompt = build_follow_up_prompt(
            original_question, "Answer.", evaluation, real_context
        )
        assert FOLLOW_UP_SYSTEM_PROMPT in prompt
        assert FOLLOW_UP_OUTPUT_INSTRUCTIONS in prompt

    def test_prompt_does_not_dump_raw_json(
        self, real_context, original_question, evaluation
    ) -> None:
        prompt = build_follow_up_prompt(
            original_question, "Answer.", evaluation, real_context
        )
        assert '"member"' not in prompt
        assert '"missions"' not in prompt


class TestStructureSafeParsing:
    """Tests for structured-output parsing (markdown fences)."""

    def test_accepts_fenced_json(self, real_context, original_question, evaluation) -> None:
        raw = "```json\n" + _valid_follow_up_json() + "\n```"
        fake = FakeLLMProvider(response=raw)
        result = FollowUpGenerator(fake).generate(
            original_question, "Answer.", evaluation, real_context
        )

        assert result.question == "Can you explain how you would handle the edge case you mentioned?"

    def test_accepts_null_metadata(self, real_context, original_question, evaluation) -> None:
        raw = json.dumps(
            {"question": "How would you improve that?", "curriculum_day": None,
             "topic": None, "difficulty": None}
        )
        fake = FakeLLMProvider(response=raw)
        result = FollowUpGenerator(fake).generate(
            original_question, "Answer.", evaluation, real_context
        )

        assert result.question == "How would you improve that?"
        assert result.curriculum_day is None


class TestValidationFailures:
    """Tests for invalid input/LLM output handling."""

    def test_empty_answer_rejected_before_llm(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(response=_valid_follow_up_json())
        generator = FollowUpGenerator(fake)

        with pytest.raises(QuestionValidationError, match="answer must not be empty"):
            generator.generate(original_question, "", evaluation, real_context)
        assert fake.last_prompt is None  # LLM never called

    def test_whitespace_answer_rejected(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(response=_valid_follow_up_json())
        with pytest.raises(QuestionValidationError, match="answer must not be empty"):
            FollowUpGenerator(fake).generate(
                original_question, "   \n  ", evaluation, real_context
            )

    def test_empty_llm_response_rejected(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(response="")
        with pytest.raises(QuestionValidationError, match="empty response"):
            FollowUpGenerator(fake).generate(
                original_question, "Answer.", evaluation, real_context
            )

    def test_invalid_json_rejected(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(response="not json")
        with pytest.raises(QuestionValidationError, match="not valid JSON"):
            FollowUpGenerator(fake).generate(
                original_question, "Answer.", evaluation, real_context
            )

    def test_missing_question_rejected(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(response=json.dumps({"topic": "x"}))
        with pytest.raises(QuestionValidationError, match="'question'"):
            FollowUpGenerator(fake).generate(
                original_question, "Answer.", evaluation, real_context
            )

    def test_empty_question_rejected(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(response=json.dumps({"question": "   "}))
        with pytest.raises(QuestionValidationError, match="'question'"):
            FollowUpGenerator(fake).generate(
                original_question, "Answer.", evaluation, real_context
            )

    def test_invented_curriculum_day_rejected(
        self, real_context, original_question, evaluation
    ) -> None:
        raw = _valid_follow_up_json(curriculum_day=999)
        fake = FakeLLMProvider(response=raw)
        with pytest.raises(QuestionValidationError, match="not in the supplied context"):
            FollowUpGenerator(fake).generate(
                original_question, "Answer.", evaluation, real_context
            )

    def test_non_int_curriculum_day_rejected(
        self, real_context, original_question, evaluation
    ) -> None:
        raw = _valid_follow_up_json(curriculum_day="7")
        fake = FakeLLMProvider(response=raw)
        with pytest.raises(QuestionValidationError, match="'curriculum_day' must be an integer"):
            FollowUpGenerator(fake).generate(
                original_question, "Answer.", evaluation, real_context
            )

    def test_invalid_topic_type_rejected(
        self, real_context, original_question, evaluation
    ) -> None:
        raw = _valid_follow_up_json(topic=123)
        fake = FakeLLMProvider(response=raw)
        with pytest.raises(QuestionValidationError, match="'topic' must be a string"):
            FollowUpGenerator(fake).generate(
                original_question, "Answer.", evaluation, real_context
            )

    def test_invalid_difficulty_type_rejected(
        self, real_context, original_question, evaluation
    ) -> None:
        raw = _valid_follow_up_json(difficulty=5)
        fake = FakeLLMProvider(response=raw)
        with pytest.raises(QuestionValidationError, match="'difficulty' must be a string"):
            FollowUpGenerator(fake).generate(
                original_question, "Answer.", evaluation, real_context
            )


class TestProviderErrors:
    """Tests that provider errors propagate cleanly."""

    def test_provider_error_propagates(
        self, real_context, original_question, evaluation
    ) -> None:
        fake = FakeLLMProvider(error=LLMGenerationError("API unavailable"))
        with pytest.raises(LLMError):
            FollowUpGenerator(fake).generate(
                original_question, "Answer.", evaluation, real_context
            )

    def test_generator_does_not_require_gemini(self) -> None:
        """The generator depends on LLMProvider, never on GeminiProvider."""
        import inspect

        source = inspect.getsource(FollowUpGenerator)
        assert "GeminiProvider" not in source
        assert "google" not in source