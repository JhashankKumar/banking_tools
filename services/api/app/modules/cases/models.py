from datetime import datetime
from enum import StrEnum

from sqlalchemy import Column, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import SyntheticRecordMixin, pg_enum


class CaseStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    ESCALATED = "escalated"
    CLOSED = "closed"


case_transactions = Table(
    "case_transactions",
    Base.metadata,
    Column("case_id", Text, ForeignKey("cases.id"), primary_key=True),
    Column("transaction_id", Text, ForeignKey("transactions.id"), primary_key=True),
)


class Case(SyntheticRecordMixin, Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    status: Mapped[CaseStatus] = mapped_column(pg_enum(CaseStatus, "case_status"))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Alert(SyntheticRecordMixin, Base):
    """A detection signal for review. Not a finding of fraud."""

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    case_id: Mapped[str | None] = mapped_column(ForeignKey("cases.id"), index=True)
    rule_id: Mapped[str] = mapped_column(Text)
    rule_version: Mapped[str] = mapped_column(Text)
    transaction_id: Mapped[str | None] = mapped_column(ForeignKey("transactions.id"))
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    summary: Mapped[str] = mapped_column(Text)
