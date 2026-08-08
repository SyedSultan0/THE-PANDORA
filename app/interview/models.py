"""Pydantic models for interview components."""

from typing import Literal

from pydantic import BaseModel, Field

Correctness = Literal["CORRECT", "PARTIAL", "INCORRECT"]
Confidence = Literal["LOW", "MEDIUM", "HIGH"]


class GeneratedQuestion(BaseModel):
    """A single generated interview question with optional metadata.

    The question text is always present. Metadata fields are optional and
    only included when the supplied context supports them.
    """

    question: str = Field(min_length=1)
    curriculum_day: int | None = Field(default=None, ge=1)
    topic: str | None = None
    difficulty: str | None = None


class EvaluationResult(BaseModel):
    """Structured evaluation of a candidate's answer.

    Score scale (0-10):
        0     = no meaningful answer
        1-3   = very weak
        4-5   = partial/basic understanding
        6-7   = good understanding
        8-9   = strong understanding
        10    = excellent/deep understanding
    """

    score: int = Field(ge=0, le=10)
    correctness: Correctness
    strengths: list[str]
    gaps: list[str]
    reasoning: str = Field(min_length=1)
    confidence: Confidence | None = None