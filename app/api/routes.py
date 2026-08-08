"""FastAPI routing for the interview API.

This module implements ``POST /api/interview`` on top of the existing
:class:`SessionManager`, :class:`InterviewEngine`, existing context builder,
and interview components. The router is built by :func:`create_router` so the
LLM provider can be injected — tests inject fake providers, while
``app.main`` injects the real provider.
"""

from fastapi import APIRouter, HTTPException

from app.api.models import InterviewRequest, InterviewResponse
from app.api.session_manager import SessionManager, SessionNotFoundError
from app.context import InterviewContext, build_interview_context
from app.interview import (
    AnswerEvaluator,
    EngineError,
    FeedbackGenerator,
    FollowUpGenerator,
    InterviewEngine,
    QuestionGenerator,
)
from app.llm.base import LLMProvider
from app.loaders.curriculum import load_curriculum
from app.models.curriculum import Curriculum


def create_router(
    llm: LLMProvider,
    session_manager: SessionManager | None = None,
    curriculum: Curriculum | None = None,
) -> APIRouter:
    """Build the ``/api/interview`` router.

    Args:
        llm: The LLM provider shared by all interview components.
        session_manager: Optional :class:`SessionManager`; a fresh one is
            created when omitted.
        curriculum: Optional preloaded curriculum; the default dataset is
            loaded when omitted.

    Returns:
        A FastAPI router exposing ``POST /api/interview``.
    """
    router = APIRouter()
    sessions = session_manager if session_manager is not None else SessionManager()
    curriculum_data = curriculum if curriculum is not None else load_curriculum()

    # The engine exposes its state publicly but not its context. Keep a
    # sessionId -> context map so the final FeedbackGenerator can consume the
    # same context that drove the interview.
    contexts: dict[str, InterviewContext] = {}

    @router.post("/api/interview", response_model=InterviewResponse)
    def interview(request: InterviewRequest) -> InterviewResponse:
        """Handle one turn of an interview session."""
        if request.candidate is not None:
            # ------------------------- Initial request -------------------------
            if sessions.has_session(request.sessionId):
                raise HTTPException(
                    status_code=409,
                    detail=f"Session '{request.sessionId}' already exists.",
                )

            context = build_interview_context(request.candidate, curriculum_data)
            engine = InterviewEngine(
                question_generator=QuestionGenerator(llm),
                answer_evaluator=AnswerEvaluator(llm),
                follow_up_generator=FollowUpGenerator(llm),
                context=context,
            )
            sessions.create_session(request.sessionId, engine)
            contexts[request.sessionId] = context

            turn = engine.start()
            if turn.question is None:
                raise HTTPException(
                    status_code=500,
                    detail="Interview engine did not return a question.",
                )
            return InterviewResponse(
                reply=turn.question.question,
                done=False,
                feedback=None,
            )

        # ------------------------ Subsequent request --------------------------
        try:
            engine = sessions.get_session(request.sessionId)
        except SessionNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{request.sessionId}' not found.",
            ) from None

        try:
            turn = engine.submit_answer(request.message or "")
        except EngineError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from None

        if not turn.done:
            if turn.question is None:
                raise HTTPException(
                    status_code=500,
                    detail="Interview engine did not return a question.",
                )
            return InterviewResponse(
                reply=turn.question.question,
                done=False,
                feedback=None,
            )

        feedback = FeedbackGenerator(llm).generate(
            contexts[request.sessionId], engine.state
        )
        return InterviewResponse(
            reply=feedback.summary,
            done=True,
            feedback=feedback,
        )

    return router