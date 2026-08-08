"""Pydantic request/response models for the organizer API contract.

These models define the wire format for ``POST /api/interview``. They reuse
the existing domain models — ``Candidate`` for the initial request payload and
``FeedbackResult`` for the final response — so the candidate schema and the
feedback contract are not duplicated.

Routing and session management are intentionally NOT implemented here.
"""

from pydantic import BaseModel, Field, field_validator, model_validator

from app.interview.models import FeedbackResult
from app.models.candidates import Candidate


class InterviewRequest(BaseModel):
    """A single request to the interview endpoint.

    Supports BOTH shapes of the organizer contract:

    * Initial request: ``{"sessionId": "...", "candidate": {...}}``
    * Subsequent request: ``{"sessionId": "...", "message": "..."}``

    Exactly one of ``candidate`` or ``message`` must be provided.
    """

    sessionId: str = Field(min_length=1)
    candidate: Candidate | None = None
    message: str | None = None

    @field_validator("sessionId")
    @classmethod
    def _session_id_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("sessionId must be a non-empty string")
        return value

    @field_validator("message")
    @classmethod
    def _message_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("message must be a non-empty string")
        return value

    @model_validator(mode="after")
    def _exactly_one_of_candidate_or_message(self) -> "InterviewRequest":
        has_candidate = self.candidate is not None
        has_message = self.message is not None
        if has_candidate == has_message:
            raise ValueError(
                "Exactly one of 'candidate' or 'message' must be provided."
            )
        return self


class InterviewResponse(BaseModel):
    """A single response from the interview endpoint.

    ``reply`` is the text to present to the candidate. ``done`` indicates
    whether the interview is complete. ``feedback`` is present only when the
    interview is complete and reuses the existing :class:`FeedbackResult`.
    """

    reply: str = Field(min_length=1)
    done: bool = False
    feedback: FeedbackResult | None = None

    @field_validator("reply")
    @classmethod
    def _reply_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reply must be a non-empty string")
        return value