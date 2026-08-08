
"""Tests for the POST /api/interview FastAPI endpoint.

No real Gemini/API calls are made — a fake LLMProvider is injected into the
router via ``create_router``.
"""

import json
import re
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import create_router
from app.api.session_manager import SessionManager
from app.interview.prompts import (
    EVALUATION_SYSTEM_PROMPT,
    FEEDBACK_SYSTEM_PROMPT,
    FOLLOW_UP_SYSTEM_PROMPT,
    QUESTION_SYSTEM_PROMPT,
)
from app.interview.errors import QuestionValidationError
from app.llm.base import LLMProvider
from app.llm.errors import LLMGenerationError
from app.loaders.candidates import load_candidates
from app.loaders.curriculum import load_curriculum


# ---------------------------------------------------------------------------
# Fake LLM provider
# ---------------------------------------------------------------------------


class FakeLLMProvider(LLMProvider):
    """A scriptable fake LLM that returns valid JSON for each prompt type."""

    def __init__(self) -> None:
        self.question_calls = 0
        self.feedback_calls = 0
        self.fail_with: Exception | None = None

    def _maybe_fail(self) -> None:
        """Raise a configured failure before returning a response."""
        if self.fail_with is not None:
            raise self.fail_with

    def generate(self, prompt: str) -> str:
        self._maybe_fail()
        if FEEDBACK_SYSTEM_PROMPT in prompt:
            self.feedback_calls += 1
            return json.dumps(
                {
                    "summary": "Good performance overall.",
                    "strengths": ["Clear answers"],
                    "gaps": ["Deepen system design"],
                    "next": ["Review the day 29 content"],
                }
            )

        if EVALUATION_SYSTEM_PROMPT in prompt:
            return json.dumps(
                {
                    "score": 8,
                    "correctness": "CORRECT",
                    "strengths": ["Accurate explanation"],
                    "gaps": [],
                    "reasoning": "Strong answer.",
                    "confidence": "HIGH",
                }
            )

        if FOLLOW_UP_SYSTEM_PROMPT in prompt:
            day = self._extract_day(prompt)
            return json.dumps(
                {
                    "question": "Follow-up question?",
                    "curriculum_day": day,
                    "topic": "Follow-up",
                    "difficulty": "hard",
                }
            )

        if QUESTION_SYSTEM_PROMPT in prompt:
            self.question_calls += 1
            day = self._extract_day(prompt)
            return json.dumps(
                {
                    "question": f"Question {self.question_calls} for day {day}",
                    "curriculum_day": day,
                    "topic": f"Day {day}",
                    "difficulty": "medium",
                }
            )

        raise AssertionError("Unknown prompt type received by the fake LLM.")

    @staticmethod
    def _extract_day(prompt: str) -> int | None:
        """Extract the first curriculum day listed in the prompt."""
        match = re.search(r"- Day (\d+) \[module", prompt)
        return int(match.group(1)) if match else None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api() -> SimpleNamespace:
    """A fresh FastAPI app with a fake LLM and an observable SessionManager."""
    llm = FakeLLMProvider()
    sessions = SessionManager()
    curriculum = load_curriculum()

    app = FastAPI()
    app.include_router(
        create_router(llm=llm, session_manager=sessions, curriculum=curriculum)
    )
    client = TestClient(app)

    return SimpleNamespace(client=client, sessions=sessions, llm=llm)


@pytest.fixture
def candidate_payload() -> dict:
    """A valid candidate payload matching the real organizer dataset."""
    candidate = load_candidates().candidates[0]  # CAND-001 Sarah Johnson
    return candidate.model_dump(mode="json")


def _start(client: TestClient, session_id: str, candidate: dict):
    """Send the initial interview request."""
    return client.post("/api/interview", json={"sessionId": session_id, "candidate": candidate})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestInitialRequest:
    """Tests for the initial interview request."""

    def test_initial_request_returns_200(self, api, candidate_payload) -> None:
        response = _start(api.client, "sess-init", candidate_payload)
        assert response.status_code == 200

    def test_initial_request_returns_a_question(self, api, candidate_payload) -> None:
        response = _start(api.client, "sess-question", candidate_payload)
        data = response.json()
        assert data["reply"]
        assert data["done"] is False
        assert data["feedback"] is None

    def test_session_is_stored(self, api, candidate_payload) -> None:
        _start(api.client, "sess-stored", candidate_payload)
        assert api.sessions.has_session("sess-stored")


class TestSubsequentRequest:
    """Tests for the subsequent answer submission."""

    def test_subsequent_answer_returns_next_question(self, api, candidate_payload) -> None:
        _start(api.client, "sess-next", candidate_payload)
        response = api.client.post(
            "/api/interview", json={"sessionId": "sess-next", "message": "My answer."}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["reply"]
        assert data["done"] is False
        assert data["feedback"] is None


class TestErrors:
    """Tests for error handling."""

    def test_duplicate_session_returns_409(self, api, candidate_payload) -> None:
        _start(api.client, "sess-dup", candidate_payload)
        response = _start(api.client, "sess-dup", candidate_payload)
        assert response.status_code == 409

    def test_unknown_session_returns_404(self, api) -> None:
        response = api.client.post(
            "/api/interview", json={"sessionId": "sess-unknown", "message": "Hello."}
        )
        assert response.status_code == 404

    def test_invalid_request_is_rejected(self, api) -> None:
        # Neither 'candidate' nor 'message' is provided.
        response = api.client.post("/api/interview", json={"sessionId": "sess-invalid"})
        assert response.status_code == 422

    def test_empty_message_is_rejected(self, api) -> None:
        response = api.client.post(
            "/api/interview", json={"sessionId": "sess-empty", "message": "   "}
        )
        assert response.status_code == 422


class TestCompletion:
    """Tests for the final completed interview response."""

    def test_final_response_contains_done_and_feedback(self, api, candidate_payload) -> None:
        _start(api.client, "sess-complete", candidate_payload)

        for _ in range(8):
            response = api.client.post(
                "/api/interview",
                json={"sessionId": "sess-complete", "message": "Solid answer."},
            )
            assert response.status_code == 200

        data = response.json()
        assert data["done"] is True
        assert data["feedback"] is not None
        assert data["feedback"]["summary"]
        assert isinstance(data["feedback"]["strengths"], list)
        assert isinstance(data["feedback"]["gaps"], list)
        assert isinstance(data["feedback"]["next"], list)

    def test_interview_terminates_within_max_boundary(self, api, candidate_payload) -> None:
        """The interview must terminate within the max question boundary and
        return the structured final response — it can never run unbounded."""
        _start(api.client, "sess-bounded", candidate_payload)

        done_response = None
        for _ in range(20):  # safety cap well above the 15-question max
            response = api.client.post(
                "/api/interview",
                json={"sessionId": "sess-bounded", "message": "Answer."},
            )
            assert response.status_code == 200
            data = response.json()
            if data["done"] is True:
                done_response = data
                break

        assert done_response is not None, "Interview did not terminate within the max boundary"
        assert done_response["done"] is True
        assert done_response["feedback"] is not None
        assert done_response["feedback"]["summary"]
        assert isinstance(done_response["feedback"]["strengths"], list)
        assert isinstance(done_response["feedback"]["gaps"], list)
        assert isinstance(done_response["feedback"]["next"], list)

    def test_no_question_generated_after_completion(self, api, candidate_payload) -> None:
        """After done=true, submitting another answer must be rejected — no
        further interview question is generated."""
        _start(api.client, "sess-after", candidate_payload)

        done_response = None
        for _ in range(20):
            response = api.client.post(
                "/api/interview",
                json={"sessionId": "sess-after", "message": "Answer."},
            )
            assert response.status_code == 200
            data = response.json()
            if data["done"] is True:
                done_response = data
                break

        assert done_response is not None
        assert done_response["done"] is True

        # Submitting after completion must be rejected (engine error → 400).
        response = api.client.post(
            "/api/interview",
            json={"sessionId": "sess-after", "message": "Too late."},
        )
        assert response.status_code == 400
        assert "detail" in response.json()


class TestErrorHandling:
    """Tests for the centralized API exception-handling layer."""

    def test_error_responses_contain_detail(self, api) -> None:
        response = api.client.post(
            "/api/interview", json={"sessionId": "sess-detail", "message": "Hello."}
        )
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_domain_validation_failure_returns_400(self, api, candidate_payload) -> None:
        # A QuestionValidationError (an InterviewError) raised during start()
        # must be mapped to a clean HTTP 400.
        api.llm.fail_with = QuestionValidationError("invalid question output")
        response = _start(api.client, "sess-domain", candidate_payload)
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_llm_error_returns_controlled_500(self, api, candidate_payload) -> None:
        api.llm.fail_with = LLMGenerationError("provider exploded")
        response = _start(api.client, "sess-llm", candidate_payload)
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        # Internal provider details must not leak.
        assert "exploded" not in data["detail"]

    def test_successful_flow_still_works(self, api, candidate_payload) -> None:
        response = _start(api.client, "sess-flow", candidate_payload)
        assert response.status_code == 200
        response = api.client.post(
            "/api/interview", json={"sessionId": "sess-flow", "message": "Answer."}
        )
        assert response.status_code == 200
        assert response.json()["done"] is False
