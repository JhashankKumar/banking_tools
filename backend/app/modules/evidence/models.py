from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import SyntheticRecordMixin, pg_enum


class EvidenceType(StrEnum):
    TRANSACTION = "transaction"
    ALERT = "alert"
    RULE_RESULT = "rule_result"
    DERIVED_CALCULATION = "derived_calculation"


class EvidenceLabel(StrEnum):
    OBSERVED_FACT = "observed_fact"
    DERIVED_FACT = "derived_fact"
    INDICATOR = "indicator"
    HYPOTHESIS = "hypothesis"
    UNKNOWN = "unknown"


class Evidence(SyntheticRecordMixin, Base):
    """A citable pointer to a source record within one case. AI citations use these IDs."""

    __tablename__ = "evidence"
    __table_args__ = (
        CheckConstraint(r"id ~ '^EV-[A-Z0-9-]+$'", name="id_format"),
        UniqueConstraint("case_id", "source_table", "source_record_id", name="uq_evidence_source"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    evidence_type: Mapped[EvidenceType] = mapped_column(pg_enum(EvidenceType, "evidence_type"))
    source_table: Mapped[str] = mapped_column(Text)
    source_record_id: Mapped[str] = mapped_column(Text)
    label: Mapped[EvidenceLabel] = mapped_column(pg_enum(EvidenceLabel, "evidence_label"))
