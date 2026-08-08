"""Interview context building layer.

Combines candidate profile, curriculum, mission history, learning signals,
and optional interview state into a structured :class:`InterviewContext`
that the future Interview Engine can consume.
"""

from app.context.builder import build_interview_context
from app.context.curriculum_helpers import (
    get_day,
    get_days_for_missions,
    get_module,
    get_module_days,
    module_day_numbers,
)
from app.context.models import (
    CandidateProfile,
    CurriculumDayInfo,
    InterviewContext,
    InterviewState,
    LearningSignals,
    MissionRecord,
    MissionState,
)

__all__ = [
    "CandidateProfile",
    "CurriculumDayInfo",
    "InterviewContext",
    "InterviewState",
    "LearningSignals",
    "MissionRecord",
    "MissionState",
    "build_interview_context",
    "get_day",
    "get_days_for_missions",
    "get_module",
    "get_module_days",
    "module_day_numbers",
]