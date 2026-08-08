"""Tests for the in-memory SessionManager (Member 2, Milestone 2).

No real InterviewEngine or LLM calls are made — a minimal fake engine is used.
"""

import pytest

from app.api import (
    SessionAlreadyExistsError,
    SessionError,
    SessionManager,
    SessionNotFoundError,
)


class FakeEngine:
    """A minimal stand-in for an InterviewEngine.

    Only exposes the small surface the SessionManager and the future API
    route need: a mutable ``state`` and a ``submit_answer`` that records
    answers. No LLM/generation logic is involved.
    """

    def __init__(self, label: str = "engine") -> None:
        self.label = label
        self.answers: list[str] = []

    def submit_answer(self, answer: str) -> None:
        self.answers.append(answer)


@pytest.fixture
def manager() -> SessionManager:
    return SessionManager()


@pytest.fixture
def engine() -> FakeEngine:
    return FakeEngine()


class TestCreateSession:
    """Tests for creating sessions."""

    def test_create_session(self, manager, engine) -> None:
        manager.create_session("abc-123", engine)
        assert manager.has_session("abc-123") is True

    def test_duplicate_session_rejected(self, manager, engine) -> None:
        manager.create_session("abc-123", engine)
        with pytest.raises(SessionAlreadyExistsError, match="already exists"):
            manager.create_session("abc-123", FakeEngine())

    def test_duplicate_does_not_overwrite(self, manager, engine) -> None:
        manager.create_session("abc-123", engine)
        with pytest.raises(SessionAlreadyExistsError):
            manager.create_session("abc-123", FakeEngine())
        # The original engine is still the one registered.
        assert manager.get_session("abc-123") is engine


class TestGetSession:
    """Tests for retrieving sessions."""

    def test_get_session_returns_engine(self, manager, engine) -> None:
        manager.create_session("abc-123", engine)
        assert manager.get_session("abc-123") is engine

    def test_unknown_session_raises(self, manager) -> None:
        with pytest.raises(SessionNotFoundError, match="not found"):
            manager.get_session("does-not-exist")

    def test_unknown_session_is_session_error(self, manager) -> None:
        with pytest.raises(SessionError):
            manager.get_session("does-not-exist")


class TestHasSession:
    """Tests for has_session."""

    def test_has_session_true_after_create(self, manager, engine) -> None:
        manager.create_session("abc-123", engine)
        assert manager.has_session("abc-123") is True

    def test_has_session_false_before_create(self, manager) -> None:
        assert manager.has_session("abc-123") is False

    def test_has_session_false_after_remove(self, manager, engine) -> None:
        manager.create_session("abc-123", engine)
        manager.remove_session("abc-123")
        assert manager.has_session("abc-123") is False


class TestRemoveSession:
    """Tests for removing sessions."""

    def test_remove_session(self, manager, engine) -> None:
        manager.create_session("abc-123", engine)
        manager.remove_session("abc-123")
        assert manager.has_session("abc-123") is False

    def test_remove_unknown_session_raises(self, manager) -> None:
        with pytest.raises(SessionNotFoundError, match="not found"):
            manager.remove_session("does-not-exist")

    def test_remove_unknown_session_is_session_error(self, manager) -> None:
        with pytest.raises(SessionError):
            manager.remove_session("does-not-exist")


class TestMultipleSessions:
    """Tests for multiple independent sessions."""

    def test_multiple_independent_sessions(self, manager) -> None:
        engine_a = FakeEngine("A")
        engine_b = FakeEngine("B")
        manager.create_session("session-a", engine_a)
        manager.create_session("session-b", engine_b)

        assert manager.get_session("session-a") is engine_a
        assert manager.get_session("session-b") is engine_b

    def test_state_remains_attached_to_same_engine(self, manager) -> None:
        engine = FakeEngine()
        manager.create_session("abc-123", engine)

        # Simulate the future API route: retrieve and advance the engine.
        retrieved = manager.get_session("abc-123")
        retrieved.submit_answer("First answer.")
        retrieved.submit_answer("Second answer.")

        # The same engine instance retains its state across retrievals.
        assert manager.get_session("abc-123") is engine
        assert engine.answers == ["First answer.", "Second answer."]

    def test_removing_one_session_does_not_affect_another(self, manager) -> None:
        engine_a = FakeEngine("A")
        engine_b = FakeEngine("B")
        manager.create_session("session-a", engine_a)
        manager.create_session("session-b", engine_b)

        manager.remove_session("session-a")

        assert manager.has_session("session-a") is False
        assert manager.has_session("session-b") is True
        assert manager.get_session("session-b") is engine_b