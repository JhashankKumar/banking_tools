"""Builders for TransactionFact shared by the rule tests."""

from datetime import datetime
from decimal import Decimal

from app.modules.detection.facts import Conversion, PartyKey, TransactionFact
from app.modules.transactions.models import TransactionStatus


def fact(
    tx_id: str,
    source: PartyKey,
    destination: PartyKey,
    amount: str,
    at: datetime,
    *,
    currency: str = "INR",
    status: TransactionStatus = TransactionStatus.SETTLED,
    reversed_by: tuple[str, ...] = (),
    reverses: str | None = None,
    converted: Conversion | None = None,
) -> TransactionFact:
    return TransactionFact(
        id=tx_id,
        source=source,
        destination=destination,
        amount=Decimal(amount),
        currency=currency,
        occurred_at=at,
        status=status,
        reversed_by=reversed_by,
        reverses=reverses,
        converted=converted,
    )
