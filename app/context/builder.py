"""Interview context builder.

Combines a candidate, the curriculum, and optional interview state into a
normalized :class:`InterviewContext` for the future Interview Engine.
"""

from app.context.models import (
    CandidateProfile,
    CurriculumDayInfo,
    InterviewContext,
    InterviewState,
    LearningSignals,
    MissionRecord,
)
from app.models.candidates import AttemptedMission, Candidate, SkippedMission
from app.models.curriculum import Curriculum


def build_interview_context(
    candidate: Candidate,
    curriculum: Curriculum,
    interview_state: InterviewState | None = None,
) -> InterviewContext:
    """Build a normalized interview context for a candidate.

    Args:
        candidate: The candidate (with member, missions, signals).
        curriculum: The loaded curriculum.
        interview_state: Optional interview progress/history. When omitted,
            an empty :class:`InterviewState` is used.

    Returns:
        A fully populated :class:`InterviewContext`.
    """
    missions = [_mission_record(m) for m in candidate.missions]
    curriculum_days = _curriculum_day_infos(candidate, curriculum)

    return InterviewContext(
        candidate=CandidateProfile(
            id=candidate.member.id,
            name=candidate.member.name,
            jobRole=candidate.member.jobRole,
            yearsExperience=candidate.member.yearsExperience,
            education=candidate.member.education,
            status=candidate.member.status,
        ),
        missions=missions,
        signals=LearningSignals(
            commitDays=candidate.signals.commitDays,
            missionsCompleted=candidate.signals.missionsCompleted,
            missionsFirstTry=candidate.signals.missionsFirstTry,
        ),
        curriculumDays=curriculum_days,
        interviewState=interview_state if interview_state is not None else InterviewState(),
    )


def _mission_record(mission: AttemptedMission | SkippedMission) -> MissionRecord:
    """Convert a raw mission variant into a normalized MissionRecord."""
    if isinstance(mission, SkippedMission):
        return MissionRecord(day=mission.day, title=mission.title, state="SKIPPED")

    # AttemptedMission
    state = "PASSED" if mission.passed else "FAILED"
    return MissionRecord(
        day=mission.day,
        title=mission.title,
        state=state,
        attempts=mission.attempts,
    )


def _curriculum_day_infos(
    candidate: Candidate, curriculum: Curriculum
) -> list[CurriculumDayInfo]:
    """Build CurriculumDayInfo entries for the candidate's mission days.

    Only days that exist in the curriculum are included. The containing
    module is resolved from the curriculum's module day ranges.
    """
    mission_days = sorted({m.day for m in candidate.missions})
    by_day = {day.day: day for day in curriculum.days}

    infos: list[CurriculumDayInfo] = []
    for day_number in mission_days:
        day = by_day.get(day_number)
        if day is None:
            continue

        module = _module_for_day(curriculum, day_number)
        infos.append(
            CurriculumDayInfo(
                day=day.day,
                title=day.title,
                type=day.type,
                moduleNumber=module.n if module else 0,
                moduleTitle=module.title if module else "",
                objectives=day.objectives,
            )
        )
    return infos


def _module_for_day(curriculum: Curriculum, day_number: int):
    """Return the module containing the given day, or ``None``."""
    for module in curriculum.modules:
        start, end = module.days
        if start <= day_number <= end:
            return module
    return None