"""Interview engine orchestrating questions, evaluation, and follow-ups.

The engine is an ORCHESTRATOR. It owns the interview state machine and
decides what happens next, but delegates generation/evaluation to injected
components. It has no HTTP, FastAPI, or session concepts.
"""

from app.context.models import InterviewContext
from app.interview.answer_evaluator import AnswerEvaluator
from app.interview.engine_models import Difficulty, EngineState, EngineTurn
from app.interview.errors import EngineError
from app.interview.follow_up_generator import FollowUpGenerator
from app.interview.models import EvaluationResult, GeneratedQuestion
from app.interview.question_generator import QuestionGenerator

MIN_QUESTIONS = 8
MIN_DAYS_COVERED = 4
MAX_QUESTIONS = 15
MAX_FOLLOW_UP_STREAK = 3

_DIFFICULTY_ORDER = ("easy", "medium", "hard")


class InterviewEngine:
    """A multi-turn technical interview state machine.

    The engine exposes ``start()`` and ``submit_answer()``. It reuses the
    injected QuestionGenerator, AnswerEvaluator, and FollowUpGenerator.
    """

    def __init__(
        self,
        question_generator: QuestionGenerator,
        answer_evaluator: AnswerEvaluator,
        follow_up_generator: FollowUpGenerator,
        context: InterviewContext,
        *,
        min_questions: int = MIN_QUESTIONS,
        min_days: int = MIN_DAYS_COVERED,
        max_questions: int = MAX_QUESTIONS,
        max_follow_up_streak: int = MAX_FOLLOW_UP_STREAK,
        state: EngineState | None = None,
    ) -> None:
        self._question_generator = question_generator
        self._answer_evaluator = answer_evaluator
        self._follow_up_generator = follow_up_generator
        self._context = context
        self._min_questions = min_questions
        self._min_days = min_days
        self._max_questions = max_questions
        self._max_follow_up_streak = max_follow_up_streak
        self._state = state if state is not None else EngineState()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def state(self) -> EngineState:
        """Return the current engine state (for inspection/persistence)."""
        return self._state

    def start(self) -> EngineTurn:
        """Start the interview and generate/present the first question.

        Returns:
            An EngineTurn with the first question.

        Raises:
            EngineError: If the interview has already started.
        """
        if self._state.status != "NOT_STARTED":
            raise EngineError(
                f"Cannot start: interview is already in state '{self._state.status}'."
            )

        day = self._select_next_day()
        question = self._generate_main_question(day)
        self._present_question(question, is_follow_up=False)
        return self._build_turn(is_follow_up=False)

    def submit_answer(self, answer: str) -> EngineTurn:
        """Submit a candidate answer and advance the interview.

        Args:
            answer: The candidate's answer to the current question.

        Returns:
            An EngineTurn with the next question, or a completed turn.

        Raises:
            EngineError: If the engine is not waiting for an answer, or the
                answer is empty.
        """
        self._ensure_waiting_for_answer()
        if not answer or not answer.strip():
            raise EngineError("Candidate answer must not be empty.")

        current = self._state.current_question
        if current is None:
            raise EngineError("No current question to answer.")

        # 1. Evaluate and record the answer.
        evaluation = self._answer_evaluator.evaluate(current, answer, self._context)
        self._state.answers.append(answer)
        self._state.evaluations.append(evaluation)

        # 2. Update difficulty based on the evaluation.
        self._state.current_difficulty = self._updated_difficulty(
            self._state.current_difficulty, evaluation
        )

        # 3. Complete only after enough answers AND curriculum coverage.
        if self._is_complete():
            self._state.status = "COMPLETED"
            self._state.current_question = None
            return EngineTurn(
                question=None,
                done=True,
                question_number=self._state.question_count,
                is_follow_up=False,
                evaluation=evaluation,
            )

        # 4. Decide whether a follow-up is appropriate.
        if self._should_follow_up(evaluation):
            follow_up = self._follow_up_generator.generate(
                current, answer, evaluation, self._context
            )
            self._present_question(follow_up, is_follow_up=True)
            return self._build_turn(is_follow_up=True, evaluation=evaluation)

        # 5. Otherwise select a new curriculum day and generate a main question.
        day = self._select_next_day()
        question = self._generate_main_question(day)
        self._present_question(question, is_follow_up=False)
        return self._build_turn(is_follow_up=False, evaluation=evaluation)

    # ------------------------------------------------------------------
    # Question generation / selection
    # ------------------------------------------------------------------

    def _generate_main_question(self, day: int | None) -> GeneratedQuestion:
        """Generate a main question for the given curriculum day (or None).

        The context is narrowed to the selected day's curriculum info so the
        generator stays on-topic. The full context (candidate, missions,
        signals) is preserved.
        """
        if day is None:
            return self._question_generator.generate(self._context)
        filtered = [info for info in self._context.curriculumDays if info.day == day]
        target_context = self._context.model_copy(update={"curriculumDays": filtered})
        return self._question_generator.generate(target_context)

    def _select_next_day(self) -> int | None:
        """Select the next curriculum day deterministically.

        Priority:
        1. Days from FAILED/SKIPPED missions not yet covered.
        2. Days from PASSED missions not yet covered.
        3. Any other available day not yet covered.
        4. Fall back to the first available day if all are covered.
        """
        available = sorted({info.day for info in self._context.curriculumDays})
        if not available:
            return None

        covered = self._state.days_covered
        by_state = {"FAILED": [], "SKIPPED": [], "PASSED": []}
        for info in self._context.curriculumDays:
            if info.day in covered:
                continue
            for mission in self._context.missions:
                if mission.day == info.day:
                    by_state[mission.state].append(info.day)
                    break

        for state_key in ("FAILED", "SKIPPED", "PASSED"):
            candidates = sorted(set(by_state[state_key]))
            if candidates:
                return candidates[0]

        # Any uncovered day (not tied to a mission).
        uncovered = [d for d in available if d not in covered]
        if uncovered:
            return uncovered[0]

        # All covered — fall back to first available day.
        return available[0]

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def _present_question(self, question: GeneratedQuestion, *, is_follow_up: bool) -> None:
        """Record a presented question and advance the state."""
        self._state.questions_presented.append(question)
        self._state.question_count += 1
        self._state.current_question = question
        if question.curriculum_day is not None:
            self._state.days_covered.add(question.curriculum_day)
        # Track the consecutive follow-up streak; a main question resets it.
        self._state.follow_up_streak = (
            self._state.follow_up_streak + 1 if is_follow_up else 0
        )
        self._state.status = "WAITING_FOR_ANSWER"

    def _build_turn(
        self, *, is_follow_up: bool, evaluation: EvaluationResult | None = None
    ) -> EngineTurn:
        """Build the EngineTurn for the current state."""
        return EngineTurn(
            question=self._state.current_question,
            done=False,
            question_number=self._state.question_count,
            is_follow_up=is_follow_up,
            evaluation=evaluation,
        )

    def _is_complete(self) -> bool:
        """Return True when the interview should finish.

        The interview completes when BOTH minimum requirements are satisfied
        (at least ``min_questions`` answered and at least ``min_days`` distinct
        curriculum days covered), OR when the hard maximum question boundary is
        reached so the interview can never run unbounded.
        """
        minimums_met = (
            len(self._state.answers) >= self._min_questions
            and len(self._state.days_covered) >= self._min_days
        )
        max_reached = self._state.question_count >= self._max_questions
        return minimums_met or max_reached

    # ------------------------------------------------------------------
    # Policies
    # ------------------------------------------------------------------

    def _should_follow_up(self, evaluation: EvaluationResult) -> bool:
        """Decide whether a follow-up is appropriate for this evaluation.

        A follow-up is generated only when the answer is INCORRECT or PARTIAL
        AND the consecutive follow-up streak has not reached the configured
        cap. This prevents an unbounded chain of follow-ups on the same topic.
        """
        if evaluation.correctness not in {"INCORRECT", "PARTIAL"}:
            return False
        return self._state.follow_up_streak < self._max_follow_up_streak

    def _updated_difficulty(
        self, current: Difficulty, evaluation: EvaluationResult
    ) -> Difficulty:
        """Adjust difficulty deterministically based on the evaluation.

        Policy:
        - score >= 8  → increase difficulty
        - score 4-7   → maintain difficulty
        - score < 4   → decrease difficulty
        Difficulty never goes below easy or above hard.
        """
        idx = _DIFFICULTY_ORDER.index(current)
        if evaluation.score >= 8:
            return _DIFFICULTY_ORDER[min(idx + 1, len(_DIFFICULTY_ORDER) - 1)]  # type: ignore[return-value]
        if evaluation.score < 4:
            return _DIFFICULTY_ORDER[max(idx - 1, 0)]  # type: ignore[return-value]
        return current

    # ------------------------------------------------------------------
    # Safety
    # ------------------------------------------------------------------

    def _ensure_waiting_for_answer(self) -> None:
        if self._state.status == "NOT_STARTED":
            raise EngineError("Cannot submit an answer before the interview has started.")
        if self._state.status == "COMPLETED":
            raise EngineError("Cannot submit an answer after the interview is complete.")
        if self._state.current_question is None:
            raise EngineError("No current question to answer.")