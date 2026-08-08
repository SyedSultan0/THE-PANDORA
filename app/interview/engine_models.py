"""Pydantic models for the interview engine state and turns.

These models are pure domain objects: they contain no HTTP, session, or
provider concepts. ``EngineState`` is fully serializable so an interview can
be persisted and later restored.
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.interview.models import EvaluationResult, GeneratedQuestion

EngineStatus = Literal["NOT_STARTED", "WAITING_FOR_ANSWER", "COMPLETED"]
Difficulty = Literal["easy", "medium", "hard"]

DIFFICULTY_ORDER: tuple[Difficulty, ...] = ("easy", "medium", "hard")


class EngineTurn(BaseModel):
    """The result of an engine operation (``start`` or ``submit_answer``).

    ``question`` is the question to present to the candidate, or ``None``
    when the interview is complete. ``done`` indicates completion.
    """

    question: GeneratedQuestion | None = None
    done: bool = False
    question_number: int = Field(default=0, ge=0)
    is_follow_up: bool = False
    evaluation: EvaluationResult | None = None


class EngineState(BaseModel):
    """Serializable state of an interview engine session.

    Contains everything required to reconstruct an in-progress interview:
    status, the pending question, the full question/answer/evaluation
    history, curriculum coverage, difficulty, and the question count.
    """

    status: EngineStatus = "NOT_STARTED"
    current_question: GeneratedQuestion | None = None
    questions_presented: list[GeneratedQuestion] = Field(default_factory=list)
    answers: list[str] = Field(default_factory=list)
    evaluations: list[EvaluationResult] = Field(default_factory=list)
    days_covered: set[int] = Field(default_factory=set)
    current_difficulty: Difficulty = "medium"
    question_count: int = Field(default=0, ge=0)
    follow_up_streak: int = Field(default=0, ge=0)
