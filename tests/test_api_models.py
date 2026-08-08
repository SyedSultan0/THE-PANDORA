"""Tests for the API request/response models (Member 2).

These tests validate the organizer contract wire models only. No routing,
session management, or LLM calls are involved.
"""

import pytest
from pydantic import ValidationError

from app.api import InterviewRequest, InterviewResponse
from app.interview.models import FeedbackResult
from app.loaders.candidates import load_candidates
from app.models.candidates import Candidate


@pytest.fixture(scope="module")
def real_candidate() -> Candidate:
    """A real candidate from the organizer's candidates.json."""
    return load_candidates().candidates[0]


class TestInterviewRequest:
    """Tests for the request model supporting both contract shapes."""

    def test_valid_initial_request(self, real_candidate) -> None:
        request = InterviewRequest(
            sessionId="abc-123",
            candidate=real_candidate,
        )
        assert request.sessionId == "abc-123"
        assert request.candidate is real_candidate
        assert request.message is None

    def test_valid_subsequent_request(self) -> None:
        request = InterviewRequest(
            sessionId="abc-123",
            message="My answer to the question.",
        )
        assert request.sessionId == "abc-123"
        assert request.message == "My answer to the question."
        assert request.candidate is None

    def test_initial_request_round_trips_candidate(self, real_candidate) -> None:
        request = InterviewRequest(
            sessionId="abc-123",
            candidate=real_candidate,
        )
        dumped = request.model_dump()
        assert dumped["sessionId"] == "abc-123"
        assert dumped["candidate"]["member"]["id"] == "CAND-001"
        assert dumped["message"] is None

    def test_missing_session_id_rejected(self, real_candidate) -> None:
        with pytest.raises(ValidationError, match="sessionId"):
            InterviewRequest(candidate=real_candidate)  # type: ignore[call-arg]

    def test_empty_session_id_rejected(self, real_candidate) -> None:
        with pytest.raises(ValidationError, match="sessionId"):
            InterviewRequest(sessionId="", candidate=real_candidate)

    def test_whitespace_session_id_rejected(self, real_candidate) -> None:
        with pytest.raises(ValidationError, match="sessionId"):
            InterviewRequest(sessionId="   ", candidate=real_candidate)

    def test_invalid_candidate_rejected(self) -> None:
        with pytest.raises(ValidationError, match="candidate"):
            InterviewRequest(
                sessionId="abc-123",
                candidate={"member": {"id": "x"}, "missions": [], "signals": {}},
            )

    def test_both_candidate_and_message_rejected(self, real_candidate) -> None:
        with pytest.raises(ValidationError, match="Exactly one"):
            InterviewRequest(
                sessionId="abc-123",
                candidate=real_candidate,
                message="Also a message.",
            )

    def test_neither_candidate_nor_message_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Exactly one"):
            InterviewRequest(sessionId="abc-123")

    def test_blank_message_rejected(self) -> None:
        with pytest.raises(ValidationError, match="message"):
            InterviewRequest(sessionId="abc-123", message="   ")


class TestInterviewResponse:
    """Tests for the response model."""

    def test_valid_non_final_response(self) -> None:
        response = InterviewResponse(
            reply="Welcome. Let's begin your interview.",
            done=False,
        )
        assert response.reply == "Welcome. Let's begin your interview."
        assert response.done is False
        assert response.feedback is None

    def test_valid_final_response_with_feedback(self) -> None:
        feedback = FeedbackResult(
            summary="Solid performance.",
            strengths=["Clear reasoning"],
            gaps=["Weak on embeddings"],
            next=["Review embeddings"],
        )
        response = InterviewResponse(
            reply="Interview completed.",
            done=True,
            feedback=feedback,
        )
        assert response.reply == "Interview completed."
        assert response.done is True
        assert response.feedback is feedback

    def test_final_response_round_trips_feedback(self) -> None:
        response = InterviewResponse(
            reply="Interview completed.",
            done=True,
            feedback=FeedbackResult(
                summary="Solid performance.",
                strengths=["Clear reasoning"],
                gaps=["Weak on embeddings"],
                next=["Review embeddings"],
            ),
        )
        dumped = response.model_dump()
        assert dumped["reply"] == "Interview completed."
        assert dumped["done"] is True
        assert dumped["feedback"] == {
            "summary": "Solid performance.",
            "strengths": ["Clear reasoning"],
            "gaps": ["Weak on embeddings"],
            "next": ["Review embeddings"],
        }

    def test_invalid_feedback_rejected(self) -> None:
        with pytest.raises(ValidationError, match="feedback"):
            InterviewResponse(
                reply="Interview completed.",
                done=True,
                feedback={"summary": "", "strengths": [], "gaps": [], "next": []},
            )

    def test_empty_reply_rejected(self) -> None:
        with pytest.raises(ValidationError, match="reply"):
            InterviewResponse(reply="", done=False)

    def test_whitespace_reply_rejected(self) -> None:
        with pytest.raises(ValidationError, match="reply"):
            InterviewResponse(reply="   ", done=False)

    def test_done_defaults_to_false(self) -> None:
        response = InterviewResponse(reply="Hello.")
        assert response.done is False
        assert response.feedback is None