"""Question generation using the provider-agnostic LLM abstraction.

The generator depends only on :class:`LLMProvider` and the normalized
:class:`InterviewContext`; it never imports a concrete provider.
"""

from typing import Any

from pydantic import ValidationError

from app.context.models import InterviewContext
from app.interview._parsing import generate_json, parse_json_object
from app.interview.errors import QuestionValidationError
from app.interview.models import GeneratedQuestion
from app.interview.prompts import build_question_prompt
from app.llm.base import LLMProvider
from app.llm.errors import LLMError


class QuestionGenerator:
    """Generates a single interview question from an InterviewContext."""

    def __init__(self, llm: LLMProvider) -> None:
        """Initialize with any LLMProvider implementation."""
        self._llm = llm

    def generate(self, context: InterviewContext) -> GeneratedQuestion:
        """Generate the next interview question for the given context.

        Args:
            context: The normalized interview context (candidate, missions,
                curriculum days, and optional interview state).

        Returns:
            A validated :class:`GeneratedQuestion`.

        Raises:
            QuestionValidationError: If the LLM returns empty/invalid output
                or references a curriculum day not in the supplied context.
            LLMError: If the underlying provider fails to generate a response.
        """
        prompt = build_question_prompt(context)

        return self._build_generated_question(
            generate_json(self._llm, prompt, QuestionValidationError), context
        )

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