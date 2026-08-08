"""Pydantic models for the candidates dataset.

Mirrors the structure of ``data/candidates.json``.

Missions come in two shapes depending on whether the candidate
attempted or skipped the mission:

* Attempted: ``{"day": int, "title": str, "passed": bool, "attempts": int}``
* Skipped:   ``{"day": int, "title": str, "skipped": true}``
"""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, BeforeValidator, Field


class Member(BaseModel):
    """A candidate's identifying profile."""

    id: str
    name: str
    jobRole: str
    yearsExperience: int = Field(ge=0)
    education: str
    status: str


class AttemptedMission(BaseModel):
    """A mission the candidate actually attempted."""

    day: int = Field(ge=1)
    title: str
    passed: bool
    attempts: int = Field(ge=1)


class SkippedMission(BaseModel):
    """A mission the candidate skipped."""

    day: int = Field(ge=1)
    title: str
    skipped: Literal[True]


def _route_mission(value):
    """Route a raw mission dict to the correct variant model.

    Skips to ``SkippedMission`` when the payload carries a truthy
    ``skipped`` flag; otherwise parses as an ``AttemptedMission``.
    """
    if isinstance(value, (AttemptedMission, SkippedMission)):
        return value
    if not isinstance(value, dict):
        raise ValueError("Mission must be a JSON object.")
    if value.get("skipped") is True:
        return SkippedMission.model_validate(value)
    return AttemptedMission.model_validate(value)


MissionVariant = Annotated[
    Union[AttemptedMission, SkippedMission], BeforeValidator(_route_mission)
]


class Signals(BaseModel):
    """Aggregate signal metrics for a candidate."""

    commitDays: int = Field(ge=0)
    missionsCompleted: int = Field(ge=0)
    missionsFirstTry: int = Field(ge=0)


class Candidate(BaseModel):
    """A single candidate and their curriculum missions."""

    member: Member
    missions: list[MissionVariant]
    signals: Signals


class Candidates(BaseModel):
    """The full candidates dataset."""

    candidates: list[Candidate]