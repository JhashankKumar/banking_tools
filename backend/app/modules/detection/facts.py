"""Immutable transaction facts that rules evaluate. Built from records; rules never touch the DB."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.modules.transactions.models import TransactionStatus

PartyKey = tuple[Literal["account", "beneficiary"], str]

# Only these normalized statuses represent money that actually moved (ADR 0001 #8 context).
COMPLETED_STATUSES = frozenset({TransactionStatus.POSTED, TransactionStatus.SETTLED})


@dataclass(frozen=True)
class Conversion:
    """The amount in another currency stated by the source record, and the rate it applied."""

    amount: Decimal
    currency: str
    rate: Decimal


@dataclass(frozen=True)
class TransactionFact:
    id: str
    source: PartyKey
    destination: PartyKey
    amount: Decimal
    currency: str
    occurred_at: datetime
    status: TransactionStatus
    reversed_by: tuple[str, ...] = ()  # IDs of reversal records pointing at this transaction
    reverses: str | None = None  # set when this record is itself a reversal of another
    rail: str | None = None
    reference: str | None = None
    converted: Conversion | None = None  # only when the record states it; never computed here


def amount_in(fact: TransactionFact, currency: str) -> Decimal | None:
    """The amount in `currency`: as recorded, or as the record's own stated conversion."""
    if fact.currency == currency:
        return fact.amount
    if fact.converted is not None and fact.converted.currency == currency:
        return fact.converted.amount
    return None


def is_completed(fact: TransactionFact) -> bool:
    """Completed and not undone by a later reversal record."""
    return fact.status in COMPLETED_STATUSES and not fact.reversed_by
