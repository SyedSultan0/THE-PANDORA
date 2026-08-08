"""In-memory session manager for the interview API.

The manager maintains a mapping of ``sessionId`` to an :class:`InterviewEngine`
instance so the future API route can keep an interview alive across multiple
HTTP requests. It is intentionally minimal: it only manages engine instances
and their lifecycle. It has no LLM, HTTP, FastAPI, or generation concerns.
"""

from app.interview.engine import InterviewEngine


class SessionError(Exception):
    """Base class for session-management errors."""


class SessionNotFoundError(SessionError):
    """Raised when a session ID does not exist."""


class SessionAlreadyExistsError(SessionError):
    """Raised when creating a session with an ID that already exists."""


class SessionManager:
    """Maintains ``sessionId -> InterviewEngine`` mappings in memory.

    The manager is deliberately simple and dependency-free. It does not
    create engines, call the LLM, or know anything about HTTP. The API layer
    injects fully-constructed engines via :meth:`create_session`.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, InterviewEngine] = {}

    def create_session(self, session_id: str, engine: InterviewEngine) -> None:
        """Register a new interview engine under ``session_id``.

        Args:
            session_id: The client-supplied session identifier.
            engine: The fully-constructed InterviewEngine for this session.

        Raises:
            SessionAlreadyExistsError: If ``session_id`` is already registered.
        """
        if session_id in self._sessions:
            raise SessionAlreadyExistsError(
                f"Session '{session_id}' already exists."
            )
        self._sessions[session_id] = engine

    def get_session(self, session_id: str) -> InterviewEngine:
        """Return the engine for ``session_id``.

        Args:
            session_id: The client-supplied session identifier.

        Returns:
            The InterviewEngine registered for ``session_id``.

        Raises:
            SessionNotFoundError: If ``session_id`` is not registered.
        """
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            raise SessionNotFoundError(
                f"Session '{session_id}' not found."
            ) from exc

    def remove_session(self, session_id: str) -> None:
        """Remove the engine registered under ``session_id``.

        Args:
            session_id: The client-supplied session identifier.

        Raises:
            SessionNotFoundError: If ``session_id`` is not registered.
        """
        if session_id not in self._sessions:
            raise SessionNotFoundError(
                f"Session '{session_id}' not found."
            )
        del self._sessions[session_id]

    def has_session(self, session_id: str) -> bool:
        """Return whether ``session_id`` is currently registered."""
        return session_id in self._sessions