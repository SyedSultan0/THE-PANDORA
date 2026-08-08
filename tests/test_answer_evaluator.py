"""Tests for the AnswerEvaluator and its prompt builder.

No real Gemini/API calls are made — a fake LLMProvider is used.
"""

import json

import pytest

from app.context import build_interview_context
from app.interview import (
    AnswerEvaluator,
    EvaluationResult,
    GeneratedQuestion,
    build_evaluation_prompt,
)
from app.interview.errors import EvaluationValidationError
from app.interview.prompts import (
    EVALUATION_OUTPUT_INSTRUCTIONS,
    EVALUATION_SYSTEM_PROMPT,
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


def _valid_evaluation_json(**overrides) -> str:
    payload = {
        "score": 8,
        "correctness": "CORRECT",
        "strengths": ["Clear explanation", "Correct terminology"],
        "gaps": ["Did not mention edge cases"],
        "reasoning": "Strong technical grasp shown.",
        "confidence": "HIGH",
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
def sample_question():
    return GeneratedQuestion(
        question="Explain how vector embeddings are generated.",
        curriculum_day=7,
        topic="Embeddings",
        difficulty="medium",
    )


class TestEvaluatorInteractsWithGenericProvider:
    """Tests that AnswerEvaluator uses the generic LLMProvider interface."""

    def test_accepts_any_llm_provider(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json())
        evaluator = AnswerEvaluator(fake)

        assert isinstance(evaluator._llm, LLMProvider)

    def test_valid_answer_produces_evaluation_result(
        self, real_context, sample_question
    ) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json())
        evaluator = AnswerEvaluator(fake)

        result = evaluator.evaluate(sample_question, "My answer here.", real_context)

        assert isinstance(result, EvaluationResult)
        assert result.score == 8
        assert result.correctness == "CORRECT"
        assert result.strengths == ["Clear explanation", "Correct terminology"]
        assert result.gaps == ["Did not mention edge cases"]
        assert result.reasoning == "Strong technical grasp shown."
        assert result.confidence == "HIGH"

    def test_uses_provider_generate(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json())
        evaluator = AnswerEvaluator(fake)

        evaluator.evaluate(sample_question, "Answer.", real_context)

        assert fake.last_prompt is not None


class TestPromptContent:
    """Tests for how question/answer/context are placed in the prompt."""

    def test_prompt_includes_question(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json())
        AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

        prompt = fake.last_prompt
        assert "Explain how vector embeddings are generated." in prompt
        assert "Curriculum day: 7" in prompt

    def test_prompt_includes_candidate_answer(
        self, real_context, sample_question
    ) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json())
        AnswerEvaluator(fake).evaluate(
            sample_question, "I generate embeddings by...", real_context
        )

        prompt = fake.last_prompt
        assert "I generate embeddings by..." in prompt

    def test_prompt_includes_candidate_context(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json())
        AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

        prompt = fake.last_prompt
        assert "Senior Data Engineer" in prompt
        assert "MS Computer Science" in prompt

    def test_prompt_includes_mission_history(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json())
        AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

        prompt = fake.last_prompt
        assert "Embeddings Explained" in prompt
        assert "PASSED" in prompt

    def test_prompt_contains_system_instructions(
        self, real_context, sample_question
    ) -> None:
        prompt = build_evaluation_prompt(sample_question, "Answer.", real_context)
        assert EVALUATION_SYSTEM_PROMPT in prompt
        assert EVALUATION_OUTPUT_INSTRUCTIONS in prompt

    def test_prompt_does_not_dump_raw_json(
        self, real_context, sample_question
    ) -> None:
        prompt = build_evaluation_prompt(sample_question, "Answer.", real_context)
        assert '"member"' not in prompt
        assert '"missions"' not in prompt


class TestStructureSafeParsing:
    """Tests for structured-output parsing (markdown fences, etc.)."""

    def test_accepts_fenced_json(self, real_context, sample_question) -> None:
        raw = "```json\n" + _valid_evaluation_json() + "\n```"
        fake = FakeLLMProvider(response=raw)
        result = AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

        assert result.score == 8

    def test_accepts_null_confidence(self, real_context, sample_question) -> None:
        raw = json.dumps(
            {
                "score": 5,
                "correctness": "PARTIAL",
                "strengths": ["Partial"],
                "gaps": ["Missing depth"],
                "reasoning": "Partially correct.",
                "confidence": None,
            }
        )
        fake = FakeLLMProvider(response=raw)
        result = AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

        assert result.score == 5
        assert result.correctness == "PARTIAL"
        assert result.confidence is None


class TestValidationFailures:
    """Tests for invalid input/LLM output handling."""

    def test_empty_answer_rejected_before_llm(
        self, real_context, sample_question
    ) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json())
        evaluator = AnswerEvaluator(fake)

        with pytest.raises(EvaluationValidationError, match="answer must not be empty"):
            evaluator.evaluate(sample_question, "", real_context)
        assert fake.last_prompt is None  # LLM never called

    def test_whitespace_answer_rejected(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json())
        with pytest.raises(EvaluationValidationError, match="answer must not be empty"):
            AnswerEvaluator(fake).evaluate(sample_question, "   \n  ", real_context)

    def test_empty_llm_response_rejected(
        self, real_context, sample_question
    ) -> None:
        fake = FakeLLMProvider(response="")
        with pytest.raises(EvaluationValidationError, match="empty response"):
            AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

    def test_invalid_json_rejected(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(response="not json")
        with pytest.raises(EvaluationValidationError, match="not valid JSON"):
            AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

    def test_invalid_score_rejected(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json(score=11))
        with pytest.raises(EvaluationValidationError, match="score"):
            AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

    def test_negative_score_rejected(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json(score=-1))
        with pytest.raises(EvaluationValidationError, match="score"):
            AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

    def test_invalid_correctness_rejected(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json(correctness="WRONG"))
        with pytest.raises(EvaluationValidationError, match="correctness"):
            AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

    def test_invalid_strengths_type_rejected(
        self, real_context, sample_question
    ) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json(strengths="not a list"))
        with pytest.raises(EvaluationValidationError, match="strengths"):
            AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

    def test_invalid_gaps_type_rejected(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json(gaps=123))
        with pytest.raises(EvaluationValidationError, match="gaps"):
            AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

    def test_empty_reasoning_rejected(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json(reasoning=""))
        with pytest.raises(EvaluationValidationError, match="reasoning"):
            AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

    def test_invalid_confidence_rejected(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(response=_valid_evaluation_json(confidence="UNKNOWN"))
        with pytest.raises(EvaluationValidationError, match="confidence"):
            AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)


class TestProviderErrors:
    """Tests that provider errors propagate cleanly."""

    def test_provider_error_propagates(self, real_context, sample_question) -> None:
        fake = FakeLLMProvider(error=LLMGenerationError("API unavailable"))
        with pytest.raises(LLMError):
            AnswerEvaluator(fake).evaluate(sample_question, "Answer.", real_context)

    def test_evaluator_does_not_require_gemini(self) -> None:
        """The evaluator depends on LLMProvider, never on GeminiProvider."""
        import inspect

        source = inspect.getsource(AnswerEvaluator)
        assert "GeminiProvider" not in source
        assert "google" not in source