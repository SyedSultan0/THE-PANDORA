"""Tests for the InterviewEngine state machine.

No real Gemini/API calls are made — fake generators/evaluators are used.
"""

import pytest

from app.context import build_interview_context
from app.context.models import (
    CandidateProfile,
    CurriculumDayInfo,
    InterviewContext,
    LearningSignals,
    MissionRecord,
)
from app.interview import (
    AnswerEvaluator,
    EngineState,
    EvaluationResult,
    FollowUpGenerator,
    GeneratedQuestion,
    InterviewEngine,
    QuestionGenerator,
)
from app.interview.errors import EngineError
from app.loaders.candidates import load_candidates
from app.loaders.curriculum import load_curriculum


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeQuestionGenerator(QuestionGenerator):
    """Returns a question for the day in the (filtered) context."""

    def __init__(self) -> None:
        self.calls: list[InterviewContext] = []

    def generate(self, context: InterviewContext) -> GeneratedQuestion:
        self.calls.append(context)
        day = context.curriculumDays[0].day if context.curriculumDays else None
        return GeneratedQuestion(
            question=f"Question for day {day}",
            curriculum_day=day,
            topic=f"Topic {day}",
            difficulty="medium",
        )


class FakeAnswerEvaluator(AnswerEvaluator):
    """Returns evaluations in sequence, then a default."""

    def __init__(self, evaluations: list[EvaluationResult] | None = None) -> None:
        self.evaluations = evaluations or []
        self.index = 0
        self.calls: list[tuple] = []

    def evaluate(self, question, answer, context):
        self.calls.append((question, answer, context))
        if self.index < len(self.evaluations):
            result = self.evaluations[self.index]
            self.index += 1
            return result
        return EvaluationResult(
            score=8,
            correctness="CORRECT",
            strengths=["s"],
            gaps=[],
            reasoning="r",
            confidence="HIGH",
        )


class FakeFollowUpGenerator(FollowUpGenerator):
    """Returns a follow-up question on the same day as the original."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def generate(self, question, answer, evaluation, context):
        self.calls.append((question, answer, evaluation, context))
        return GeneratedQuestion(
            question=f"Follow-up to: {question.question}",
            curriculum_day=question.curriculum_day,
            topic=question.topic,
            difficulty=question.difficulty,
        )


def _eval(
    score: int = 8,
    correctness: str = "CORRECT",
    strengths=None,
    gaps=None,
    reasoning: str = "r",
    confidence: str | None = "HIGH",
) -> EvaluationResult:
    return EvaluationResult(
        score=score,
        correctness=correctness,
        strengths=strengths or ["s"],
        gaps=gaps or [],
        reasoning=reasoning,
        confidence=confidence,
    )


def _day_info(day: int) -> CurriculumDayInfo:
    return CurriculumDayInfo(
        day=day,
        title=f"Day {day}",
        type="BUILD",
        moduleNumber=1,
        moduleTitle="M1",
        objectives=[f"objective-{day}"],
    )


def _make_engine(
    context: InterviewContext,
    *,
    evaluations: list[EvaluationResult] | None = None,
    state: EngineState | None = None,
    min_questions: int = 8,
    min_days: int = 4,
) -> InterviewEngine:
    return InterviewEngine(
        question_generator=FakeQuestionGenerator(),
        answer_evaluator=FakeAnswerEvaluator(evaluations),
        follow_up_generator=FakeFollowUpGenerator(),
        context=context,
        min_questions=min_questions,
        min_days=min_days,
        state=state,
    )


def _four_day_context() -> InterviewContext:
    return InterviewContext(
        candidate=CandidateProfile(
            id="C1",
            name="Test",
            jobRole="Engineer",
            yearsExperience=2,
            education="BS",
            status="ACTIVE",
        ),
        missions=[],
        signals=LearningSignals(
            commitDays=1, missionsCompleted=1, missionsFirstTry=1
        ),
        curriculumDays=[_day_info(d) for d in (1, 2, 3, 4)],
    )


def _mission_priority_context() -> InterviewContext:
    return InterviewContext(
        candidate=CandidateProfile(
            id="C1",
            name="Test",
            jobRole="Engineer",
            yearsExperience=2,
            education="BS",
            status="ACTIVE",
        ),
        missions=[
            MissionRecord(day=5, title="Day 5", state="PASSED"),
            MissionRecord(day=3, title="Day 3", state="FAILED"),
            MissionRecord(day=7, title="Day 7", state="SKIPPED"),
        ],
        signals=LearningSignals(
            commitDays=1, missionsCompleted=1, missionsFirstTry=1
        ),
        curriculumDays=[_day_info(d) for d in (3, 5, 7)],
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_context():
    candidate = load_candidates().candidates[0]
    curriculum = load_curriculum()
    return build_interview_context(candidate, curriculum)


@pytest.fixture
def engine(real_context):
    return _make_engine(real_context)


@pytest.fixture
def small_context():
    """A context with only 2 curriculum days (for completion-boundary tests)."""
    return InterviewContext(
        candidate=CandidateProfile(
            id="C1",
            name="Test",
            jobRole="Engineer",
            yearsExperience=2,
            education="BS",
            status="ACTIVE",
        ),
        missions=[],
        signals=LearningSignals(
            commitDays=1, missionsCompleted=1, missionsFirstTry=1
        ),
        curriculumDays=[_day_info(1), _day_info(2)],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestInitialState:
    """Tests for the initial NOT_STARTED state."""

    def test_initial_state_is_not_started(self, engine) -> None:
        assert engine.state.status == "NOT_STARTED"
        assert engine.state.question_count == 0
        assert engine.state.current_question is None
        assert engine.state.answers == []
        assert engine.state.evaluations == []
        assert engine.state.days_covered == set()


class TestEngineStart:
    """Tests for engine startup."""

    def test_engine_starts_correctly(self, engine) -> None:
        turn = engine.start()
        assert turn.done is False
        assert turn.question is not None
        assert turn.question_number == 1
        assert engine.state.status == "WAITING_FOR_ANSWER"

    def test_first_question_is_generated(self, engine) -> None:
        turn = engine.start()
        assert turn.question is not None
        assert "Question for day" in turn.question.question

    def test_engine_enters_waiting_for_answer(self, engine) -> None:
        engine.start()
        assert engine.state.status == "WAITING_FOR_ANSWER"
        assert engine.state.current_question is not None

    def test_start_twice_raises(self, engine) -> None:
        engine.start()
        with pytest.raises(EngineError, match="already in state"):
            engine.start()


class TestAnswerSubmission:
    """Tests for answer evaluation and recording."""

    def test_submit_before_start_raises(self, engine) -> None:
        with pytest.raises(EngineError, match="before the interview has started"):
            engine.submit_answer("Too early.")

    def test_empty_answer_raises(self, engine) -> None:
        engine.start()
        with pytest.raises(EngineError, match="empty"):
            engine.submit_answer("")
        with pytest.raises(EngineError, match="empty"):
            engine.submit_answer("   ")

    def test_candidate_answer_is_evaluated(self, engine) -> None:
        engine.start()
        engine.submit_answer("My answer.")
        assert len(engine.state.evaluations) == 1

    def test_answer_and_evaluation_are_recorded(self, engine) -> None:
        engine.start()
        engine.submit_answer("My answer.")
        assert len(engine.state.answers) == 1
        assert engine.state.answers[0] == "My answer."
        assert len(engine.state.evaluations) == 1

    def test_strong_correct_moves_to_new_question(self, engine) -> None:
        engine.start()
        turn = engine.submit_answer("Good answer.")
        assert turn.done is False
        assert turn.question is not None
        assert turn.is_follow_up is False
        assert len(engine.state.questions_presented) == 2

    def test_follow_up_generated_for_incorrect(self, real_context) -> None:
        engine = _make_engine(
            real_context,
            evaluations=[_eval(correctness="INCORRECT", score=2)],
        )
        engine.start()
        turn = engine.submit_answer("Wrong answer.")
        assert turn.is_follow_up is True
        assert turn.question is not None
        assert "Follow-up" in turn.question.question

    def test_follow_up_generated_for_partial(self, real_context) -> None:
        engine = _make_engine(
            real_context,
            evaluations=[_eval(correctness="PARTIAL", score=5)],
        )
        engine.start()
        turn = engine.submit_answer("Partial answer.")
        assert turn.is_follow_up is True

    def test_follow_up_counts_toward_total(self, real_context) -> None:
        engine = _make_engine(
            real_context,
            evaluations=[_eval(correctness="PARTIAL", score=5)],
        )
        engine.start()
        engine.submit_answer("Partial answer.")
        assert engine.state.question_count == 2


class TestDifficulty:
    """Tests for difficulty adjustment."""

    def test_difficulty_increases_after_strong(self, real_context) -> None:
        engine = _make_engine(
            real_context,
            evaluations=[_eval(score=9, correctness="CORRECT")],
        )
        engine.start()
        assert engine.state.current_difficulty == "medium"
        engine.submit_answer("Good.")
        assert engine.state.current_difficulty == "hard"

    def test_difficulty_decreases_after_weak(self, real_context) -> None:
        engine = _make_engine(
            real_context,
            evaluations=[_eval(score=2, correctness="INCORRECT")],
        )
        engine.start()
        assert engine.state.current_difficulty == "medium"
        engine.submit_answer("Bad.")
        assert engine.state.current_difficulty == "easy"

    def test_difficulty_stays_in_bounds(self, real_context) -> None:
        engine = _make_engine(
            real_context,
            evaluations=[_eval(score=2, correctness="INCORRECT")],
            state=EngineState(current_difficulty="easy"),
        )
        engine.start()
        engine.submit_answer("Bad.")
        assert engine.state.current_difficulty == "easy"

    def test_difficulty_never_exceeds_hard(self, real_context) -> None:
        engine = _make_engine(
            real_context,
            evaluations=[_eval(score=9, correctness="CORRECT")],
            state=EngineState(current_difficulty="hard"),
        )
        engine.start()
        engine.submit_answer("Great.")
        assert engine.state.current_difficulty == "hard"


class TestCurriculumDayCoverage:
    """Tests for curriculum day coverage tracking."""

    def test_curriculum_days_are_tracked(self, real_context) -> None:
        engine = _make_engine(real_context)
        engine.start()
        assert len(engine.state.days_covered) == 1
        engine.submit_answer("Good.")
        assert len(engine.state.days_covered) == 2

    def test_only_unique_days_count(self, real_context) -> None:
        engine = _make_engine(
            real_context,
            evaluations=[_eval(correctness="PARTIAL", score=5)],
        )
        engine.start()
        engine.submit_answer("Partial.")
        assert engine.state.question_count == 2
        assert len(engine.state.days_covered) == 1

    def test_already_covered_days_not_double_counted(self, real_context) -> None:
        engine = _make_engine(
            real_context,
            evaluations=[_eval(correctness="PARTIAL", score=5)],
        )
        engine.start()
        assert len(engine.state.days_covered) == 1
        engine.submit_answer("Partial.")
        assert len(engine.state.days_covered) == 1
        assert engine.state.question_count == 2

    def test_failed_and_skipped_mission_days_prioritized(self) -> None:
        context = _mission_priority_context()
        qgen = FakeQuestionGenerator()
        engine = InterviewEngine(
            question_generator=qgen,
            answer_evaluator=FakeAnswerEvaluator(),
            follow_up_generator=FakeFollowUpGenerator(),
            context=context,
        )

        turn = engine.start()
        assert turn.question is not None
        assert turn.question.curriculum_day == 3

        turn = engine.submit_answer("Answer.")
        assert turn.question is not None
        assert turn.question.curriculum_day == 7

        turn = engine.submit_answer("Answer.")
        assert turn.question is not None
        assert turn.question.curriculum_day == 5

    def test_no_invented_curriculum_days(self, real_context) -> None:
        engine = _make_engine(real_context)
        available = {info.day for info in real_context.curriculumDays}

        engine.start()
        for _ in range(5):
            engine.submit_answer("Answer.")

        for question in engine.state.questions_presented:
            assert question.curriculum_day in available

        for call_context in engine._question_generator.calls:  # noqa: SLF001
            for info in call_context.curriculumDays:
                assert info.day in available


class TestQuestionCount:
    """Tests for question counting."""

    def test_question_count_matches_presented(self, engine) -> None:
        engine.start()
        for _ in range(3):
            engine.submit_answer("Answer.")
        assert engine.state.question_count == len(engine.state.questions_presented)
        assert engine.state.question_count == 4


class TestCompletion:
    """Tests for interview completion rules."""

    def test_eighth_question_is_presented_and_answerable(self) -> None:
        engine = _make_engine(_four_day_context())
        engine.start()
        for _ in range(6):
            engine.submit_answer("Answer.")

        turn = engine.submit_answer("Answer.")
        assert turn.done is False
        assert turn.question is not None
        assert turn.question_number == 8
        assert engine.state.status == "WAITING_FOR_ANSWER"

        turn = engine.submit_answer("Final answer.")
        assert turn.done is True
        assert engine.state.status == "COMPLETED"

    def test_does_not_complete_when_eighth_question_generated(self) -> None:
        engine = _make_engine(_four_day_context())
        engine.start()
        for _ in range(6):
            engine.submit_answer("Answer.")

        turn = engine.submit_answer("Answer.")
        assert turn.question_number == 8
        assert turn.done is False
        assert len(engine.state.answers) == 7

    def test_completion_requires_both_questions_and_days(self, small_context) -> None:
        engine = _make_engine(small_context)
        engine.start()
        for _ in range(7):
            engine.submit_answer("Answer.")

        turn = engine.submit_answer("Answer.")
        assert len(engine.state.answers) == 8
        assert len(engine.state.days_covered) == 2
        assert turn.done is False
        assert engine.state.status == "WAITING_FOR_ANSWER"

    def test_submit_after_completion_raises(self) -> None:
        engine = _make_engine(_four_day_context())
        engine.start()
        for _ in range(8):
            engine.submit_answer("Answer.")

        with pytest.raises(EngineError, match="after the interview is complete"):
            engine.submit_answer("Too late.")


class TestStateSerialization:
    """Tests for EngineState persistence."""

    def test_engine_state_can_be_serialized_and_restored(self, real_context) -> None:
        qgen = FakeQuestionGenerator()
        evaluator = FakeAnswerEvaluator()
        follow_up = FakeFollowUpGenerator()
        engine = InterviewEngine(
            question_generator=qgen,
            answer_evaluator=evaluator,
            follow_up_generator=follow_up,
            context=real_context,
        )

        engine.start()
        engine.submit_answer("First answer.")
        serialized = engine.state.model_dump_json()
        restored_state = EngineState.model_validate_json(serialized)

        restored_engine = InterviewEngine(
            question_generator=qgen,
            answer_evaluator=evaluator,
            follow_up_generator=follow_up,
            context=real_context,
            state=restored_state,
        )

        assert restored_engine.state == engine.state
        assert restored_engine.state.status == "WAITING_FOR_ANSWER"
        assert len(restored_engine.state.answers) == 1

        turn = restored_engine.submit_answer("Second answer.")
        assert turn.done is False
        assert turn.question is not None
