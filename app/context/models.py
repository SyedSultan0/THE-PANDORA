"""Pydantic models for the interview context.

These models are a normalized representation combining candidate profile,
mission history, learning signals, curriculum information, and optional
interview state. They are intentionally separate from the raw data models
in ``app.models`` so the future Interview Engine consumes a clean,
purpose-built structure.
"""

from typing import Literal

from pydantic import BaseModel, Field

MissionState = Literal["PASSED", "FAILED", "SKIPPED"]


class CandidateProfile(BaseModel):
    """Normalized candidate identity/profile for personalization."""

    id: str
    name: str
    jobRole: str
    yearsExperience: int = Field(ge=0)
    education: str
    status: str


class MissionRecord(BaseModel):
    """A single mission in the candidate's history, normalized.

    ``state`` distinguishes the three possible outcomes:
    * ``PASSED`` — attempted and passed
    * ``FAILED`` — attempted but not passed
    * ``SKIPPED`` — not attempted
    """

    day: int = Field(ge=1)
    title: str
    state: MissionState
    attempts: int | None = Field(default=None, ge=1)


class LearningSignals(BaseModel):
    """Normalized aggregate learning signals."""

    commitDays: int = Field(ge=0)
    missionsCompleted: int = Field(ge=0)
    missionsFirstTry: int = Field(ge=0)


class CurriculumDayInfo(BaseModel):
    """A curriculum day with its containing module context."""

    day: int = Field(ge=1)
    title: str
    type: str
    moduleNumber: int = Field(ge=1)
    moduleTitle: str
    objectives: list[str]


class InterviewState(BaseModel):
    """Optional interview progress/history.

    Generic and independent of Member 2's session manager. The future
    Interview Engine can populate these fields as the interview proceeds.
    """

    questionsAsked: list[str] = Field(default_factory=list)
    candidateAnswers: list[str] = Field(default_factory=list)
    currentQuestionNumber: int = Field(default=0, ge=0)
    daysCovered: list[int] = Field(default_factory=list)
    currentDifficulty: str | None = None
    previousEvaluations: list[str] = Field(default_factory=list)


class InterviewContext(BaseModel):
    """The complete structured context for the future Interview Engine.

    Combines candidate profile, mission history, learning signals,
    relevant curriculum information, and optional interview state.
    """

    candidate: CandidateProfile
    missions: list[MissionRecord]
    signals: LearningSignals
    curriculumDays: list[CurriculumDayInfo]
    interviewState: InterviewState = Field(default_factory=InterviewState)