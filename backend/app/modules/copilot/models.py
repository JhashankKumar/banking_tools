import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import pg_enum


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class RunOutcome(StrEnum):
    ANSWERED = "answered"
    DECLINED = "declined"
    FAILED = "failed"
    LIMITED = "limited"


class CopilotChat(Base):
    """One conversation about one case, owned by its author."""

    __tablename__ = "copilot_chats"
    __table_args__ = (Index("ix_copilot_chats_case_author", "case_id", "author_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CopilotRun(Base):
    """Metering and outcome of one question. Never stores prompt or answer text."""

    __tablename__ = "copilot_runs"
    __table_args__ = (Index("ix_copilot_runs_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("copilot_chats.id")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    model: Mapped[str] = mapped_column(Text)
    outcome: Mapped[RunOutcome] = mapped_column(pg_enum(RunOutcome, "copilot_outcome"))
    tool_calls: Mapped[int] = mapped_column(Integer, default=0)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=Decimal("0"))
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class CopilotMessage(Base):
    """A question (user) or a validated structured answer (assistant) in a chat."""

    __tablename__ = "copilot_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("copilot_chats.id"), index=True
    )
    role: Mapped[MessageRole] = mapped_column(pg_enum(MessageRole, "copilot_role"))
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("copilot_runs.id")
    )
    question: Mapped[str | None] = mapped_column(Text)
    answer: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
