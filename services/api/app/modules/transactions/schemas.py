from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, PlainSerializer

from app.modules.transactions.models import TransactionStatus

# Money leaves the API as a fixed two-decimal string, never a float.
Money = Annotated[Decimal, PlainSerializer(lambda v: f"{v:.2f}", return_type=str)]


class PartyRef(BaseModel):
    type: Literal["account", "beneficiary"]
    id: str


class TransactionOut(BaseModel):
    id: str
    source: PartyRef
    destination: PartyRef
    amount: Money
    currency: str
    occurred_at: datetime
    status: TransactionStatus
    source_status: str
    rail: str | None
    reference: str | None
    # Untrusted source text, returned verbatim as data.
    description: str | None
    reversal_of_transaction_id: str | None
    evidence_id: str | None
