from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import SyntheticRecordMixin, pg_enum


class TransactionStatus(StrEnum):
    """Normalized status. The source system's own value is kept in `source_status`."""

    INITIATED = "initiated"
    PENDING = "pending"
    ACCEPTED = "accepted"
    POSTED = "posted"
    SETTLED = "settled"
    FAILED = "failed"
    REVERSED = "reversed"
    RETURNED = "returned"
    DISPUTED = "disputed"


class Transaction(SyntheticRecordMixin, Base):
    """A directed transfer record. Each side is exactly one account or one beneficiary."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(source_account_id, source_beneficiary_id) = 1", name="exactly_one_source"
        ),
        CheckConstraint(
            "num_nonnulls(destination_account_id, destination_beneficiary_id) = 1",
            name="exactly_one_destination",
        ),
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="currency_code"),
        CheckConstraint(
            "num_nonnulls(converted_amount, converted_currency, fx_rate) IN (0, 3)",
            name="conversion_complete",
        ),
        CheckConstraint(
            "converted_currency ~ '^[A-Z]{3}$' AND converted_currency <> currency"
            " AND converted_amount > 0 AND fx_rate > 0",
            name="conversion_valid",
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    source_account_id: Mapped[str | None] = mapped_column(ForeignKey("accounts.id"), index=True)
    source_beneficiary_id: Mapped[str | None] = mapped_column(
        ForeignKey("beneficiaries.id"), index=True
    )
    destination_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("accounts.id"), index=True
    )
    destination_beneficiary_id: Mapped[str | None] = mapped_column(
        ForeignKey("beneficiaries.id"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2, asdecimal=True))
    currency: Mapped[str] = mapped_column(String(3))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[TransactionStatus] = mapped_column(
        pg_enum(TransactionStatus, "transaction_status")
    )
    source_status: Mapped[str] = mapped_column(Text)
    rail: Mapped[str | None] = mapped_column(Text)
    reference: Mapped[str | None] = mapped_column(Text)
    # Free text from the source record. Untrusted: display it, never act on it.
    description: Mapped[str | None] = mapped_column(Text)
    reversal_of_transaction_id: Mapped[str | None] = mapped_column(ForeignKey("transactions.id"))
    # International transfers: the amount in another currency and the rate the source system
    # applied, exactly as recorded. All three or none; nothing here is ever computed.
    converted_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2, asdecimal=True))
    converted_currency: Mapped[str | None] = mapped_column(String(3))
    fx_rate: Mapped[Decimal | None] = mapped_column(Numeric(18, 6, asdecimal=True))
