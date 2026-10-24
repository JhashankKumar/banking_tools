import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.cases.models import CaseStatus
from app.modules.notes.models import NoteOrigin, NoteStatus, ReviewDecision

CLOSING_REASONS = ("No further action", "Referred externally", "Not actionable / duplicate")

Body = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20_000)]
Comment = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2_000)]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]


class NoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: Body
    source_message_id: uuid.UUID | None = None


class NoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: Body


class ReviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: ReviewDecision
    comment: Comment | None = None
    reason: Reason | None = None

    @model_validator(mode="after")
    def _required_fields(self) -> Self:
        match self.decision:
            case ReviewDecision.RETURN if not self.comment:
                raise ValueError("A comment is required to return a note")
            case ReviewDecision.APPROVE_ESCALATE if not self.reason:
                raise ValueError("A reason is required to escalate")
            case ReviewDecision.APPROVE_CLOSE if self.reason not in CLOSING_REASONS:
                raise ValueError("Choose a closing reason from the list")
            case ReviewDecision.APPROVE_CLOSE if not self.comment:
                raise ValueError("A comment is required to close a case")
            case _:
                return self


class CloseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: Reason
    comment: Comment = Field(min_length=1)

    @model_validator(mode="after")
    def _listed_reason(self) -> Self:
        if self.reason not in CLOSING_REASONS:
            raise ValueError("Choose a closing reason from the list")
        return self


class ReviewOut(BaseModel):
    decision: ReviewDecision
    version: int
    reviewer_username: str
    comment: str | None
    reason: str | None
    created_at: datetime


class VersionOut(BaseModel):
    version: int
    edited_by_username: str
    created_at: datetime


class NoteOut(BaseModel):
    id: uuid.UUID
    case_id: str
    status: NoteStatus
    origin: NoteOrigin
    author_username: str
    current_version: int
    body: str
    cited_ids: list[str]
    created_at: datetime
    updated_at: datetime
    can_edit: bool
    can_review: bool
    reviews: list[ReviewOut]
    versions: list[VersionOut]


class StatusChangeOut(BaseModel):
    from_status: CaseStatus
    to_status: CaseStatus
    actor_username: str
    reason: str
    comment: str | None
    note_id: uuid.UUID | None
    created_at: datetime


class ReviewQueueItem(BaseModel):
    note_id: uuid.UUID
    case_id: str
    case_title: str
    author_username: str
    submitted_at: datetime
