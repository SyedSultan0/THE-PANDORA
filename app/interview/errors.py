"""Application-level exceptions for interview components."""


class InterviewError(Exception):
    """Base class for interview component errors."""


class QuestionValidationError(InterviewError):
    """Raised when a generated question is invalid or cannot be parsed."""


class EvaluationValidationError(InterviewError):
    """Raised when an evaluation result is invalid or cannot be parsed."""


class EngineError(InterviewError):
    """Raised for invalid interview engine operations."""


class FeedbackValidationError(InterviewError):
    """Raised when generated feedback is invalid or cannot be parsed."""
