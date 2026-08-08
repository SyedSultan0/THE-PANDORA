"""Pydantic models for interview components."""

from pydantic import BaseModel, Field


class GeneratedQuestion(BaseModel):
    """A single generated interview question with optional metadata.

    The question text is always present. Metadata fields are optional and
    only included when the supplied context supports them.
    """

    question: str = Field(min_length=1)
    curriculum_day: int | None = Field(default=None, ge=1)
    topic: str | None = None
    difficulty: str | None = None