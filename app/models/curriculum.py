"""Pydantic models for the curriculum dataset.

Mirrors the structure of ``data/curriculum.json``.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

CurriculumDayType = Literal[
    "SETUP", "BUILD", "AI_CORE", "SHIP_IT", "LEARN", "OPTIMIZE", "CAPSTONE"
]


class CurriculumModule(BaseModel):
    """A single module grouping several days of the cohort."""

    n: int = Field(ge=1, description="Module number (1-8).")
    title: str
    days: tuple[int, int] = Field(
        description="Inclusive day range [start, end] covered by the module."
    )

    @model_validator(mode="after")
    def _validate_day_range(self) -> "CurriculumModule":
        start, end = self.days
        if start > end:
            raise ValueError(
                f"Module {self.n} day range is invalid: start ({start}) "
                f"must be <= end ({end})."
            )
        return self


class CurriculumDay(BaseModel):
    """A single day in the curriculum."""

    day: int = Field(ge=1, description="Day number (1-31).")
    title: str
    type: CurriculumDayType
    tools: list[str]
    objectives: list[str]


class Curriculum(BaseModel):
    """The full curriculum dataset."""

    cohort: str
    modules: list[CurriculumModule]
    days: list[CurriculumDay]