import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import pg_enum
from app.modules.cases.models import CaseStatus


class NoteStatus(StrEnum):
    DRAFT = "draft"
    AWAITING_REVIEW = "awaiting_review"
    RETURNED = "returned"
    APPROVED = "approved"


class NoteOrigin(StrEnum):
    AI_DRAFTED = "ai_drafted"
    WRITTEN = "written"


class ReviewDecision(StrEnum):
    RETURN = "return"
    APPROVE_KEEP_OPEN = "approve_keep_open"
    APPROVE_ESCALATE = "approve_escalate"
    APPROVE_CLOSE = "approve_close"


class CaseNote(Base):
    """A case record written by an analyst or supervisor (optionally from a copilot draft)."""

    __tablename__ = "case_notes"
    __table_args__ = (
        # At most one note awaiting review per case, even under concurrent submissions.
        Index(
            "uq_case_notes_one_pending",
            "case_id",
            unique=True,
            postgresql_where=text("status = 'awaiting_review'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    status: Mapped[NoteStatus] = mapped_column(pg_enum(NoteStatus, "note_status"))
    origin: Mapped[NoteOrigin] = mapped_column(pg_enum(NoteOrigin, "note_origin"))
    source_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("copilot_messages.id")
    )
    current_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CaseNoteVersion(Base):
    """Every saved text of a note; versions are never overwritten."""

    __tablename__ = "case_note_versions"
    __table_args__ = (UniqueConstraint("note_id", "version", name="uq_case_note_versions_note"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_notes.id"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    cited_ids: Mapped[list[str]] = mapped_column(ARRAY(Text))
    edited_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NoteReview(Base):
    __tablename__ = "note_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_notes.id"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    decision: Mapped[ReviewDecision] = mapped_column(pg_enum(ReviewDecision, "review_decision"))
    comment: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CaseStatusChange(Base):
    """Append-only history of case status changes: who, when, from → to, and why."""

    __tablename__ = "case_status_changes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    from_status: Mapped[CaseStatus] = mapped_column(pg_enum(CaseStatus, "case_status"))
    to_status: Mapped[CaseStatus] = mapped_column(pg_enum(CaseStatus, "case_status"))
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)
    note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_notes.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
