"""Tests for the interview context builder and curriculum helpers."""

import pytest
from pydantic import ValidationError

from app.context import (
    build_interview_context,
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
)
from app.loaders.candidates import load_candidates
from app.loaders.curriculum import load_curriculum
from app.models.candidates import Candidate, Member, Signals
from app.models.curriculum import Curriculum, CurriculumDay, CurriculumModule


@pytest.fixture(scope="module")
def real_curriculum() -> Curriculum:
    """The real curriculum.json loaded once for the module."""
    return load_curriculum()


@pytest.fixture(scope="module")
def real_candidates() -> list[Candidate]:
    """The real candidates.json loaded once for the module."""
    return load_candidates().candidates


class TestRealDataIntegration:
    """Integration-style tests using the real organizer JSON files."""

    def test_real_candidate_builds_context(self, real_curriculum, real_candidates) -> None:
        candidate = real_candidates[0]  # CAND-001 Sarah Johnson
        context = build_interview_context(candidate, real_curriculum)

        assert isinstance(context, InterviewContext)
        assert isinstance(context.candidate, CandidateProfile)
        assert context.candidate.id == "CAND-001"
        assert context.candidate.name == "Sarah Johnson"
        assert context.candidate.jobRole == "Senior Data Engineer"
        assert context.candidate.yearsExperience == 9
        assert context.candidate.education == "MS Computer Science"

    def test_real_candidate_missions_normalized(self, real_curriculum, real_candidates) -> None:
        candidate = real_candidates[0]
        context = build_interview_context(candidate, real_curriculum)

        assert len(context.missions) == len(candidate.missions)
        for record in context.missions:
            assert isinstance(record, MissionRecord)
            assert record.state in {"PASSED", "FAILED", "SKIPPED"}

    def test_real_candidate_signals_preserved(self, real_curriculum, real_candidates) -> None:
        candidate = real_candidates[0]
        context = build_interview_context(candidate, real_curriculum)

        assert isinstance(context.signals, LearningSignals)
        assert context.signals.commitDays == candidate.signals.commitDays
        assert context.signals.missionsCompleted == candidate.signals.missionsCompleted
        assert context.signals.missionsFirstTry == candidate.signals.missionsFirstTry

    def test_real_candidate_curriculum_days_included(self, real_curriculum, real_candidates) -> None:
        candidate = real_candidates[0]
        context = build_interview_context(candidate, real_curriculum)

        assert len(context.curriculumDays) > 0
        for info in context.curriculumDays:
            assert isinstance(info, CurriculumDayInfo)
            assert info.day >= 1
            assert info.moduleNumber >= 1
            assert info.moduleTitle

    def test_all_real_candidates_build_context(self, real_curriculum, real_candidates) -> None:
        """Every real candidate should build a valid context."""
        for candidate in real_candidates:
            context = build_interview_context(candidate, real_curriculum)
            assert isinstance(context, InterviewContext)
            assert len(context.missions) == len(candidate.missions)


class TestMissionStateRepresentation:
    """Tests for the three mission states."""

    def _make_candidate(self, missions: list) -> Candidate:
        return Candidate(
            member=Member(
                id="C1",
                name="Test",
                jobRole="Engineer",
                yearsExperience=2,
                education="BS",
                status="COMPLETED",
            ),
            missions=missions,
            signals=Signals(commitDays=5, missionsCompleted=2, missionsFirstTry=1),
        )

    def _make_curriculum(self) -> Curriculum:
        return Curriculum(
            cohort="Test",
            modules=[CurriculumModule(n=1, title="Module 1", days=(1, 3))],
            days=[
                CurriculumDay(day=1, title="Day 1", type="BUILD", tools=[], objectives=["o1"]),
                CurriculumDay(day=2, title="Day 2", type="BUILD", tools=[], objectives=["o2"]),
                CurriculumDay(day=3, title="Day 3", type="BUILD", tools=[], objectives=["o3"]),
            ],
        )

    def test_passed_mission(self) -> None:
        candidate = self._make_candidate(
            [{"day": 1, "title": "Setup", "passed": True, "attempts": 1}]
        )
        context = build_interview_context(candidate, self._make_curriculum())

        record = context.missions[0]
        assert record.state == "PASSED"
        assert record.attempts == 1

    def test_failed_mission(self) -> None:
        candidate = self._make_candidate(
            [{"day": 2, "title": "Hard Topic", "passed": False, "attempts": 4}]
        )
        context = build_interview_context(candidate, self._make_curriculum())

        record = context.missions[0]
        assert record.state == "FAILED"
        assert record.attempts == 4

    def test_skipped_mission(self) -> None:
        candidate = self._make_candidate(
            [{"day": 3, "title": "Skipped Topic", "skipped": True}]
        )
        context = build_interview_context(candidate, self._make_curriculum())

        record = context.missions[0]
        assert record.state == "SKIPPED"
        assert record.attempts is None

    def test_mixed_states_preserved(self) -> None:
        candidate = self._make_candidate(
            [
                {"day": 1, "title": "Passed", "passed": True, "attempts": 1},
                {"day": 2, "title": "Failed", "passed": False, "attempts": 3},
                {"day": 3, "title": "Skipped", "skipped": True},
            ]
        )
        context = build_interview_context(candidate, self._make_curriculum())

        states = [m.state for m in context.missions]
        assert states == ["PASSED", "FAILED", "SKIPPED"]


class TestCurriculumHelpers:
    """Tests for curriculum day/module lookup helpers."""

    def test_get_day_found(self, real_curriculum) -> None:
        day = get_day(real_curriculum, 1)
        assert day is not None
        assert day.day == 1
        assert day.title == "VS Code & Python Environment Setup"

    def test_get_day_not_found(self, real_curriculum) -> None:
        assert get_day(real_curriculum, 999) is None

    def test_get_module_found(self, real_curriculum) -> None:
        module = get_module(real_curriculum, 1)
        assert module is not None
        assert module.n == 1
        assert module.title == "Environment & Tooling"

    def test_get_module_not_found(self, real_curriculum) -> None:
        assert get_module(real_curriculum, 99) is None

    def test_module_day_numbers_inclusive(self, real_curriculum) -> None:
        """[1, 3] means days 1, 2, and 3."""
        module = get_module(real_curriculum, 1)
        assert module is not None
        assert module_day_numbers(module) == [1, 2, 3]

    def test_module_day_numbers_last_module(self, real_curriculum) -> None:
        module = get_module(real_curriculum, 8)
        assert module is not None
        assert module_day_numbers(module) == [29, 30, 31]

    def test_get_module_days(self, real_curriculum) -> None:
        days = get_module_days(real_curriculum, 1)
        assert [d.day for d in days] == [1, 2, 3]

    def test_get_module_days_unknown_module(self, real_curriculum) -> None:
        assert get_module_days(real_curriculum, 99) == []

    def test_get_days_for_missions(self, real_curriculum) -> None:
        days = get_days_for_missions(real_curriculum, [7, 1, 7, 3])
        assert [d.day for d in days] == [1, 3, 7]

    def test_get_days_for_missions_skips_unknown(self, real_curriculum) -> None:
        days = get_days_for_missions(real_curriculum, [1, 999])
        assert [d.day for d in days] == [1]


class TestInterviewState:
    """Tests for optional interview state handling."""

    def test_default_state_is_empty(self, real_curriculum, real_candidates) -> None:
        context = build_interview_context(real_candidates[0], real_curriculum)
        assert isinstance(context.interviewState, InterviewState)
        assert context.interviewState.questionsAsked == []
        assert context.interviewState.currentQuestionNumber == 0

    def test_supplied_state_is_preserved(self, real_curriculum, real_candidates) -> None:
        state = InterviewState(
            questionsAsked=["Q1", "Q2"],
            candidateAnswers=["A1", "A2"],
            currentQuestionNumber=2,
            daysCovered=[7, 8],
            currentDifficulty="medium",
            previousEvaluations=["good"],
        )
        context = build_interview_context(real_candidates[0], real_curriculum, state)

        assert context.interviewState.questionsAsked == ["Q1", "Q2"]
        assert context.interviewState.candidateAnswers == ["A1", "A2"]
        assert context.interviewState.currentQuestionNumber == 2
        assert context.interviewState.daysCovered == [7, 8]
        assert context.interviewState.currentDifficulty == "medium"
        assert context.interviewState.previousEvaluations == ["good"]

    def test_state_is_independent_of_session_manager(self) -> None:
        """InterviewState is a plain Pydantic model, no session manager needed."""
        state = InterviewState()
        assert state.model_dump() == {
            "questionsAsked": [],
            "candidateAnswers": [],
            "currentQuestionNumber": 0,
            "daysCovered": [],
            "currentDifficulty": None,
            "previousEvaluations": [],
        }


class TestInvalidInput:
    """Tests for invalid input handling."""

    def test_invalid_candidate_raises(self, real_curriculum) -> None:
        with pytest.raises(ValidationError):
            Candidate(
                member=Member(
                    id="1",
                    name="x",
                    jobRole="y",
                    yearsExperience=-1,  # invalid
                    education="z",
                    status="ACTIVE",
                ),
                missions=[],
                signals=Signals(commitDays=1, missionsCompleted=1, missionsFirstTry=1),
            )

    def test_invalid_curriculum_raises(self) -> None:
        with pytest.raises(ValidationError):
            CurriculumModule(n=1, title="Bad", days=(5, 3))  # start > end

    def test_invalid_mission_state_raises(self) -> None:
        with pytest.raises(ValidationError):
            MissionRecord(day=1, title="x", state="UNKNOWN")  # type: ignore[arg-type]

    def test_negative_attempts_raises(self) -> None:
        with pytest.raises(ValidationError):
            MissionRecord(day=1, title="x", state="PASSED", attempts=0)