"""Follow-up question generation using the provider-agnostic LLM abstraction.

The generator depends only on :class:`LLMProvider` and existing interview
models; it never imports a concrete provider. It generates ONE contextual
follow-up question when the caller requests one — it does NOT decide whether
a follow-up is needed or what the interview should do next.
"""

from typing import Any

from pydantic import ValidationError

from app.context.models import InterviewContext
from app.interview._parsing import parse_json_object
from app.interview.errors import QuestionValidationError
from app.interview.models import EvaluationResult, GeneratedQuestion
from app.interview.prompts import build_follow_up_prompt
from app.llm.base import LLMProvider
from app.llm.errors import LLMError


class FollowUpGenerator:
    """Generates a single contextual follow-up question."""

    def __init__(self, llm: LLMProvider) -> None:
        """Initialize with any LLMProvider implementation."""
        self._llm = llm

    def generate(
        self,
        question: GeneratedQuestion,
        answer: str,
        evaluation: EvaluationResult,
        context: InterviewContext,
    ) -> GeneratedQuestion:
        """Generate a follow-up question for the given turn.

        Args:
            question: The original question the candidate answered.
            answer: The candidate's answer (must be non-empty).
            evaluation: The evaluation of the candidate's answer.
            context: The normalized interview context.

        Returns:
            A validated :class:`GeneratedQuestion` representing the follow-up.

        Raises:
            QuestionValidationError: If the answer is empty, or the LLM
                returns empty/invalid output.
            LLMError: If the underlying provider fails to generate a response.
        """
        self._validate_answer(answer)

        prompt = build_follow_up_prompt(question, answer, evaluation, context)

        try:
            raw = self._llm.generate(prompt)
        except LLMError:
            raise  # provider errors propagate unchanged

        return self._build_generated_question(
            parse_json_object(raw, QuestionValidationError), context
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_answer(self, answer: str) -> None:
        """Reject empty/whitespace answers before calling the LLM."""
        if not answer or not answer.strip():
            raise QuestionValidationError("Candidate answer must not be empty.")

    def _build_generated_question(
        self, data: dict[str, Any], context: InterviewContext
    ) -> GeneratedQuestion:
        question_text = data.get("question")
        if not isinstance(question_text, str) or not question_text.strip():
            raise QuestionValidationError(
                "LLM output is missing a non-empty 'question' field."
            )

        curriculum_day = data.get("curriculum_day")
        topic = data.get("topic")
        difficulty = data.get("difficulty")

        if curriculum_day is not None:
            if not isinstance(curriculum_day, int) or isinstance(curriculum_day, bool):
                raise QuestionValidationError(
                    "'curriculum_day' must be an integer, "
                    f"got {type(curriculum_day).__name__}."
                )
            self._validate_curriculum_day(curriculum_day, context)

        if topic is not None and not isinstance(topic, str):
            raise QuestionValidationError(
                f"'topic' must be a string, got {type(topic).__name__}."
            )

        if difficulty is not None and not isinstance(difficulty, str):
            raise QuestionValidationError(
                f"'difficulty' must be a string, got {type(difficulty).__name__}."
            )

        try:
            return GeneratedQuestion(
                question=question_text.strip(),
                curriculum_day=curriculum_day,
                topic=topic,
                difficulty=difficulty,
            )
        except ValidationError as exc:
            raise QuestionValidationError(f"Generated question is invalid: {exc}") from exc

    def _validate_curriculum_day(self, day: int, context: InterviewContext) -> None:
        """Ensure the referenced curriculum day exists in the supplied context."""
        available_days = {info.day for info in context.curriculumDays}
        if day not in available_days:
            raise QuestionValidationError(
                f"'curriculum_day' references day {day}, which is not in the "
                "supplied context's available curriculum days: "
                f"{sorted(available_days)}."
            )