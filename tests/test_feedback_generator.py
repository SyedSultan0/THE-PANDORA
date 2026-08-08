"""Tests for the FeedbackGenerator and its prompt builder.

No real Gemini/API calls are made — a fake LLMProvider is used.
"""

import json

import pytest
from pydantic import ValidationError

from app.context import build_interview_context
from app.interview import (
    EngineState,
    EvaluationResult,
    FeedbackGenerator,
    FeedbackResult,
    GeneratedQuestion,
    build_feedback_prompt,
)
from app.interview.errors import FeedbackValidationError
from app.interview.prompts import (
    FEEDBACK_OUTPUT_INSTRUCTIONS,
    FEEDBACK_SYSTEM_PROMPT,
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


def _valid_feedback_json(**overrides) -> str:
    payload = {
        "summary": "Sarah demonstrated solid data engineering fundamentals.",
        "strengths": ["Clear reasoning", "Good use of terminology"],
        "gaps": ["Weak understanding of embeddings"],
        "next": ["Review the embeddings curriculum day"],
    }
    payload.update(overrides)
    return json.dumps(payload)


def _evaluation(**overrides) -> EvaluationResult:
    payload = {
        "score": 7,
        "correctness": "PARTIAL",
        "strengths": ["Clear reasoning"],
        "gaps": ["Missing depth on embeddings"],
        "reasoning": "Partial understanding shown.",
        "confidence": "MEDIUM",
    }
    payload.update(overrides)
    return EvaluationResult.model_validate(payload)


def _completed_state() -> EngineState:
    """An EngineState resembling a completed multi-turn interview."""
    q1 = GeneratedQuestion(
        question="Explain how vector embeddings are generated.",
        curriculum_day=7,
        topic="Embeddings",
        difficulty="medium",
    )
    q2 = GeneratedQuestion(
        question="What is a vector database?",
        curriculum_day=8,
        topic="Vector Databases",
        difficulty="hard",
    )
    return EngineState(
        status="COMPLETED",
        questions_presented=[q1, q2],
        answers=[
            "Embeddings are created by a model that maps text to vectors.",
            "A vector database stores and searches high-dimensional vectors.",
        ],
        evaluations=[
            _evaluation(score=6, correctness="PARTIAL"),
            _evaluation(
                score=9,
                correctness="CORRECT",
                strengths=["Precise definition"],
                gaps=[],
                confidence="HIGH",
            ),
        ],
        days_covered={7, 8},
        current_difficulty="hard",
        question_count=2,
    )


@pytest.fixture(scope="module")
def real_context():
    """A real InterviewContext built from the actual organizer data."""
    candidate = load_candidates().candidates[0]  # CAND-001 Sarah Johnson
    curriculum = load_curriculum()
    return build_interview_context(candidate, curriculum)


@pytest.fixture(scope="module")
def completed_state():
    return _completed_state()


class TestGeneratorInteractsWithGenericProvider:
    """Tests that FeedbackGenerator uses the generic LLMProvider interface."""

    def test_accepts_any_llm_provider(
        self, real_context, completed_state
    ) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json())
        generator = FeedbackGenerator(fake)

        assert isinstance(generator._llm, LLMProvider)

    def test_valid_input_produces_feedback_result(
        self, real_context, completed_state
    ) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json())
        generator = FeedbackGenerator(fake)

        result = generator.generate(real_context, completed_state)

        assert isinstance(result, FeedbackResult)
        assert result.summary == "Sarah demonstrated solid data engineering fundamentals."
        assert result.strengths == ["Clear reasoning", "Good use of terminology"]
        assert result.gaps == ["Weak understanding of embeddings"]
        assert result.next == ["Review the embeddings curriculum day"]

    def test_uses_provider_generate(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json())
        FeedbackGenerator(fake).generate(real_context, completed_state)

        assert fake.last_prompt is not None

    def test_prompt_builder_returns_single_string(
        self, real_context, completed_state
    ) -> None:
        prompt = build_feedback_prompt(real_context, completed_state)
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestPromptContent:
    """Tests for how candidate/answers/evaluations appear in the prompt."""

    def test_prompt_includes_candidate_information(
        self, real_context, completed_state
    ) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json())
        FeedbackGenerator(fake).generate(real_context, completed_state)

        prompt = fake.last_prompt
        assert "Senior Data Engineer" in prompt
        assert "9" in prompt
        assert "MS Computer Science" in prompt

    def test_prompt_includes_candidate_name(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json())
        FeedbackGenerator(fake).generate(real_context, completed_state)

        prompt = fake.last_prompt
        assert "Sarah Johnson" in prompt

    def test_prompt_includes_questions(
        self, real_context, completed_state
    ) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json())
        FeedbackGenerator(fake).generate(real_context, completed_state)

        prompt = fake.last_prompt
        assert "Explain how vector embeddings are generated." in prompt
        assert "What is a vector database?" in prompt

    def test_prompt_includes_answers(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json())
        FeedbackGenerator(fake).generate(real_context, completed_state)

        prompt = fake.last_prompt
        assert "Embeddings are created by a model that maps text to vectors." in prompt

    def test_prompt_includes_scores(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json())
        FeedbackGenerator(fake).generate(real_context, completed_state)

        prompt = fake.last_prompt
        assert "Score: 6/10" in prompt
        assert "Score: 9/10" in prompt

    def test_prompt_includes_correctness(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json())
        FeedbackGenerator(fake).generate(real_context, completed_state)

        prompt = fake.last_prompt
        assert "Correctness: PARTIAL" in prompt
        assert "Correctness: CORRECT" in prompt

    def test_prompt_includes_strengths(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json())
        FeedbackGenerator(fake).generate(real_context, completed_state)

        prompt = fake.last_prompt
        assert "Clear reasoning" in prompt
        assert "Precise definition" in prompt

    def test_prompt_includes_gaps(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json())
        FeedbackGenerator(fake).generate(real_context, completed_state)

        prompt = fake.last_prompt
        assert "Missing depth on embeddings" in prompt

    def test_prompt_includes_reasoning(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json())
        FeedbackGenerator(fake).generate(real_context, completed_state)

        prompt = fake.last_prompt
        assert "Partial understanding shown." in prompt

    def test_prompt_includes_curriculum_coverage(
        self, real_context, completed_state
    ) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json())
        FeedbackGenerator(fake).generate(real_context, completed_state)

        prompt = fake.last_prompt
        assert "Days covered: [7, 8]" in prompt
        assert "Embeddings Explained" in prompt

    def test_prompt_contains_system_instructions(
        self, real_context, completed_state
    ) -> None:
        prompt = build_feedback_prompt(real_context, completed_state)
        assert FEEDBACK_SYSTEM_PROMPT in prompt
        assert FEEDBACK_OUTPUT_INSTRUCTIONS in prompt

    def test_prompt_does_not_dump_raw_json(
        self, real_context, completed_state
    ) -> None:
        prompt = build_feedback_prompt(real_context, completed_state)
        assert '"member"' not in prompt
        assert '"missions"' not in prompt


class TestStructureSafeParsing:
    """Tests for structured-output parsing (markdown fences)."""

    def test_accepts_fenced_json(self, real_context, completed_state) -> None:
        raw = "```json\n" + _valid_feedback_json() + "\n```"
        fake = FakeLLMProvider(response=raw)
        result = FeedbackGenerator(fake).generate(real_context, completed_state)

        assert result.summary == "Sarah demonstrated solid data engineering fundamentals."

    def test_accepts_fenced_json_without_language(
        self, real_context, completed_state
    ) -> None:
        raw = "```\n" + _valid_feedback_json() + "\n```"
        fake = FakeLLMProvider(response=raw)
        result = FeedbackGenerator(fake).generate(real_context, completed_state)

        assert result.summary == "Sarah demonstrated solid data engineering fundamentals."

    def test_accepts_empty_optional_lists(
        self, real_context, completed_state
    ) -> None:
        raw = json.dumps(
            {"summary": "Okay.", "strengths": [], "gaps": [], "next": []}
        )
        fake = FakeLLMProvider(response=raw)
        result = FeedbackGenerator(fake).generate(real_context, completed_state)

        assert result.summary == "Okay."
        assert result.strengths == []
        assert result.gaps == []
        assert result.next == []


class TestValidationFailures:
    """Tests for invalid input/LLM output handling."""

    def test_empty_llm_response_rejected(
        self, real_context, completed_state
    ) -> None:
        fake = FakeLLMProvider(response="")
        with pytest.raises(FeedbackValidationError, match="empty response"):
            FeedbackGenerator(fake).generate(real_context, completed_state)

    def test_whitespace_llm_response_rejected(
        self, real_context, completed_state
    ) -> None:
        fake = FakeLLMProvider(response="   \n  ")
        with pytest.raises(FeedbackValidationError, match="empty response"):
            FeedbackGenerator(fake).generate(real_context, completed_state)

    def test_invalid_json_rejected(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(response="not json at all")
        with pytest.raises(FeedbackValidationError, match="not valid JSON"):
            FeedbackGenerator(fake).generate(real_context, completed_state)

    def test_non_object_json_rejected(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(response="[1, 2, 3]")
        with pytest.raises(FeedbackValidationError, match="must be a JSON object"):
            FeedbackGenerator(fake).generate(real_context, completed_state)

    def test_missing_summary_rejected(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(
            response=json.dumps({"strengths": ["s"], "gaps": [], "next": []})
        )
        with pytest.raises(FeedbackValidationError, match="summary"):
            FeedbackGenerator(fake).generate(real_context, completed_state)

    def test_empty_summary_rejected(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(
            response=json.dumps({"summary": "", "strengths": [], "gaps": [], "next": []})
        )
        with pytest.raises(FeedbackValidationError, match="summary"):
            FeedbackGenerator(fake).generate(real_context, completed_state)

    def test_whitespace_summary_rejected(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(
            response=json.dumps({"summary": "   ", "strengths": [], "gaps": [], "next": []})
        )
        with pytest.raises(FeedbackValidationError, match="summary"):
            FeedbackGenerator(fake).generate(real_context, completed_state)

    def test_invalid_strengths_type_rejected(
        self, real_context, completed_state
    ) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json(strengths="not a list"))
        with pytest.raises(FeedbackValidationError, match="strengths"):
            FeedbackGenerator(fake).generate(real_context, completed_state)

    def test_invalid_gaps_type_rejected(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json(gaps=123))
        with pytest.raises(FeedbackValidationError, match="gaps"):
            FeedbackGenerator(fake).generate(real_context, completed_state)

    def test_invalid_next_type_rejected(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(response=_valid_feedback_json(next={"x": 1}))
        with pytest.raises(FeedbackValidationError, match="next"):
            FeedbackGenerator(fake).generate(real_context, completed_state)

    def test_non_string_list_items_rejected(
        self, real_context, completed_state
    ) -> None:
        fake = FakeLLMProvider(
            response=_valid_feedback_json(strengths=["ok", 42])
        )
        with pytest.raises(FeedbackValidationError, match="strengths"):
            FeedbackGenerator(fake).generate(real_context, completed_state)

    def test_non_string_summary_rejected(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(
            response=_valid_feedback_json(summary=12345)
        )
        with pytest.raises(FeedbackValidationError, match="summary"):
            FeedbackGenerator(fake).generate(real_context, completed_state)


class TestProviderErrors:
    """Tests that provider errors propagate cleanly."""

    def test_provider_error_propagates(self, real_context, completed_state) -> None:
        fake = FakeLLMProvider(error=LLMGenerationError("API unavailable"))
        with pytest.raises(LLMError):
            FeedbackGenerator(fake).generate(real_context, completed_state)

    def test_generator_does_not_require_gemini(self) -> None:
        """The generator depends on LLMProvider, never on GeminiProvider."""
        import inspect

        source = inspect.getsource(FeedbackGenerator)
        assert "GeminiProvider" not in source
        assert "google" not in source


class TestFeedbackResultModel:
    """Direct tests for the FeedbackResult model."""

    def test_valid_model(self) -> None:
        result = FeedbackResult(
            summary="Summary.",
            strengths=["a"],
            gaps=["b"],
            next=["c"],
        )
        assert result.summary == "Summary."
        assert result.strengths == ["a"]
        assert result.gaps == ["b"]
        assert result.next == ["c"]

    def test_optional_lists_default_to_empty(self) -> None:
        result = FeedbackResult(summary="Summary.")
        assert result.strengths == []
        assert result.gaps == []
        assert result.next == []

    def test_empty_summary_rejected(self) -> None:
        with pytest.raises(ValidationError, match="summary"):
            FeedbackResult(summary="")

    def test_whitespace_summary_rejected(self) -> None:
        with pytest.raises(ValidationError, match="summary"):
            FeedbackResult(summary="   ")

    def test_non_list_strengths_rejected(self) -> None:
        with pytest.raises(ValidationError, match="strengths"):
            FeedbackResult(summary="S", strengths="not a list")  # type: ignore[arg-type]

    def test_non_string_item_rejected(self) -> None:
        with pytest.raises(ValidationError, match="strengths"):
            FeedbackResult(summary="S", strengths=[1])  # type: ignore[list-item]

    def test_dump_matches_organizer_contract(self) -> None:
        result = FeedbackResult(
            summary="S",
            strengths=["s"],
            gaps=["g"],
            next=["n"],
        )
        assert result.model_dump() == {
            "summary": "S",
            "strengths": ["s"],
            "gaps": ["g"],
            "next": ["n"],
        }