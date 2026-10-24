"""Customers, accounts, and beneficiaries (separate tables, see ADR 0001 #7)."""

from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import SyntheticRecordMixin, pg_enum


class AccountStatus(StrEnum):
    ACTIVE = "active"
    DORMANT = "dormant"
    FROZEN = "frozen"
    CLOSED = "closed"


class IdentifierType(StrEnum):
    ACCOUNT = "account"
    VPA = "vpa"
    CARD_TOKEN = "card_token"  # noqa: S105  (an identifier kind, not a credential)
    WALLET = "wallet"
    EXTERNAL = "external"


class Customer(SyntheticRecordMixin, Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    display_name: Mapped[str] = mapped_column(Text)


class Account(SyntheticRecordMixin, Base):
    __tablename__ = "accounts"
    __table_args__ = (CheckConstraint("currency ~ '^[A-Z]{3}$'", name="currency_code"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"))
    status: Mapped[AccountStatus] = mapped_column(pg_enum(AccountStatus, "account_status"))
    currency: Mapped[str] = mapped_column(String(3))


class Beneficiary(SyntheticRecordMixin, Base):
    __tablename__ = "beneficiaries"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    display_label: Mapped[str] = mapped_column(Text)
    identifier_type: Mapped[IdentifierType] = mapped_column(
        pg_enum(IdentifierType, "beneficiary_identifier_type")
    )
