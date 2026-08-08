"""Tests for the FastAPI application health, docs, and wiring.

No real Gemini/API calls are made — the interview route is exercised through
``create_router`` with a fake LLM provider, and the health/docs endpoints on
``app.main`` never invoke the LLM.
"""

import json
import re
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import create_router
from app.api.session_manager import SessionManager
from app.interview.prompts import QUESTION_SYSTEM_PROMPT
from app.llm.base import LLMProvider
from app.loaders.candidates import load_candidates
from app.loaders.curriculum import load_curriculum
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health endpoint (uses the real app; no LLM is invoked)
# ---------------------------------------------------------------------------


def test_health_returns_200() -> None:
    """Verify the health endpoint returns HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok() -> None:
    """Verify the health endpoint returns the expected status payload."""
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


def test_root_endpoint() -> None:
    """Verify the root endpoint returns a healthy status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "AI Interview Agent" in data["message"]


# ---------------------------------------------------------------------------
# OpenAPI / Swagger documentation
# ---------------------------------------------------------------------------


def test_docs_endpoint_returns_200() -> None:
    """Verify FastAPI serves the interactive Swagger UI."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_contains_health_endpoint() -> None:
    """Verify the OpenAPI schema includes GET /health."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "/health" in schema["paths"]
    assert "get" in schema["paths"]["/health"]


def test_openapi_contains_interview_endpoint() -> None:
    """Verify the OpenAPI schema includes POST /api/interview."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "/api/interview" in schema["paths"]
    assert "post" in schema["paths"]["/api/interview"]


# ---------------------------------------------------------------------------
# Interview route still works (fake LLM; no network calls)
# ---------------------------------------------------------------------------


class _FakeLLMProvider(LLMProvider):
    """A minimal fake LLM that returns a valid question JSON.

    The curriculum day is extracted from the prompt so it always matches
    the context the engine passed to the QuestionGenerator.
    """

    def generate(self, prompt: str) -> str:
        assert QUESTION_SYSTEM_PROMPT in prompt
        match = re.search(r"- Day (\d+) \[module", prompt)
        day = int(match.group(1)) if match else None
        return json.dumps(
            {
                "question": "What is an embedding?",
                "curriculum_day": day,
                "topic": "Embeddings",
                "difficulty": "medium",
            }
        )


@pytest.fixture
def fake_api() -> SimpleNamespace:
    """A fresh app with a fake LLM for exercising the interview route."""
    llm = _FakeLLMProvider()
    sessions = SessionManager()

    app = FastAPI()
    app.include_router(
        create_router(
            llm=llm,
            session_manager=sessions,
            curriculum=load_curriculum(),
        )
    )
    return SimpleNamespace(client=TestClient(app), sessions=sessions)


def test_interview_endpoint_still_works(fake_api) -> None:
    """Verify POST /api/interview still works with the fake LLM."""
    candidate = load_candidates().candidates[0].model_dump(mode="json")

    response = fake_api.client.post(
        "/api/interview",
        json={"sessionId": "health-sess", "candidate": candidate},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reply"]
    assert data["done"] is False
    assert data["feedback"] is None


def test_interview_error_handling_still_works(fake_api) -> None:
    """Verify POST /api/interview error handling still works."""
    response = fake_api.client.post(
        "/api/interview", json={"sessionId": "missing", "message": "Hello."}
    )
    assert response.status_code == 404
    assert "detail" in response.json()