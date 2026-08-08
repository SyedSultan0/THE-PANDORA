"""Application-level exceptions for interview components."""


class InterviewError(Exception):
    """Base class for interview component errors."""


class QuestionValidationError(InterviewError):
    """Raised when a generated question is invalid or cannot be parsed."""