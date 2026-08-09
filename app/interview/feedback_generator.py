"""Final feedback generation using the provider-agnostic LLM abstraction.

The generator depends only on :class:`LLMProvider` and existing interview
models; it never imports a concrete provider. It consumes a completed
interview (``InterviewContext`` + ``EngineState``) and produces a validated
:class:`FeedbackResult`.
"""

from typing import Any

from pydantic import ValidationError

from app.context.models import InterviewContext
from app.interview._parsing import generate_json, parse_json_object
from app.interview.engine_models import EngineState
from app.interview.errors import FeedbackValidationError
from app.interview.models import FeedbackResult
from app.interview.prompts import build_feedback_prompt
from app.llm.base import LLMProvider
from app.llm.errors import LLMError


class FeedbackGenerator:
    """Generates final interview feedback from a completed interview."""

    def __init__(self, llm: LLMProvider) -> None:
        """Initialize with any LLMProvider implementation."""
        self._llm = llm

    def generate(
        self,
        context: InterviewContext,
        state: EngineState,
    ) -> FeedbackResult:
        """Generate final feedback for a completed interview.

        Args:
            context: The normalized interview context.
            state: The completed interview engine state (questions, answers,
                evaluations, curriculum coverage, difficulty).

        Returns:
            A validated :class:`FeedbackResult`.

        Raises:
            FeedbackValidationError: If the LLM returns empty/invalid output
                or the output does not match the feedback contract.
            LLMError: If the underlying provider fails to generate a response.
        """
        prompt = build_feedback_prompt(context, state)

        return self._build_feedback_result(
            generate_json(self._llm, prompt, FeedbackValidationError)
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _build_feedback_result(self, data: dict[str, Any]) -> FeedbackResult:
        """Validate the parsed LLM output into a FeedbackResult."""
        try:
            return FeedbackResult.model_validate(data)
        except ValidationError as exc:
            raise FeedbackValidationError(
                f"Feedback result is invalid: {exc}"
            ) from exc