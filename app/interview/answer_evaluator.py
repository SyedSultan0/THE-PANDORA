"""Answer evaluation using the provider-agnostic LLM abstraction.

The evaluator depends only on :class:`LLMProvider` and existing interview
models; it never imports a concrete provider. It evaluates a candidate's
answer and returns structured information — it does NOT decide what the
next interview step should be.
"""

from typing import Any

from pydantic import ValidationError

from app.context.models import InterviewContext
from app.interview._parsing import parse_json_object
from app.interview.errors import EvaluationValidationError
from app.interview.models import EvaluationResult, GeneratedQuestion
from app.interview.prompts import build_evaluation_prompt
from app.llm.base import LLMProvider
from app.llm.errors import LLMError


class AnswerEvaluator:
    """Evaluates a candidate's answer to a generated interview question."""

    def __init__(self, llm: LLMProvider) -> None:
        """Initialize with any LLMProvider implementation."""
        self._llm = llm

    def evaluate(
        self,
        question: GeneratedQuestion,
        answer: str,
        context: InterviewContext,
    ) -> EvaluationResult:
        """Evaluate the candidate's answer to the question.

        Args:
            question: The question the candidate answered.
            answer: The candidate's answer text (must be non-empty).
            context: The normalized interview context.

        Returns:
            A validated :class:`EvaluationResult`.

        Raises:
            EvaluationValidationError: If the answer is empty, or the LLM
                returns empty/invalid output.
            LLMError: If the underlying provider fails to generate a response.
        """
        self._validate_answer(answer)

        prompt = build_evaluation_prompt(question, answer, context)

        try:
            raw = self._llm.generate(prompt)
        except LLMError:
            raise  # provider errors propagate unchanged

        return self._build_evaluation_result(
            parse_json_object(raw, EvaluationValidationError)
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_answer(self, answer: str) -> None:
        """Reject empty/whitespace answers before calling the LLM."""
        if not answer or not answer.strip():
            raise EvaluationValidationError(
                "Candidate answer must not be empty."
            )

    def _build_evaluation_result(
        self, data: dict[str, Any]
    ) -> EvaluationResult:
        """Validate the parsed LLM output into an EvaluationResult."""
        try:
            return EvaluationResult.model_validate(data)
        except ValidationError as exc:
            raise EvaluationValidationError(
                f"Evaluation result is invalid: {exc}"
            ) from exc