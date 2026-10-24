from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.modules.transactions.models import TransactionStatus
from app.modules.transactions.schemas import Money, PartyRef


class TransactionEdgeOut(BaseModel):
    """One transaction drawn as a directed edge. Shared by money paths and the case graph."""

    transaction_id: str
    kind: Literal["transfer", "reversal"]
    source: PartyRef
    destination: PartyRef
    amount: Money
    currency: str
    occurred_at: datetime
    status: TransactionStatus
    is_final: bool
    reversed_by: list[str]
    rail: str | None
    reference: str | None
    evidence_id: str | None


class PathEdgeOut(TransactionEdgeOut):
    hop: int


class MoneyPathOut(BaseModel):
    hops: int
    is_cycle: bool
    has_non_final_edges: bool
    contains_reversal: bool
    returned_by_reversal: bool
    currencies: list[str]
    started_at: datetime
    ended_at: datetime
    elapsed_seconds: int
    limitations: list[str]
    edges: list[PathEdgeOut]


class MoneyPathParams(BaseModel):
    max_hops: int
    window_hours: int


class MoneyPathsOut(BaseModel):
    case_id: str
    parameters: MoneyPathParams
    truncated: bool
    paths: list[MoneyPathOut]


class GraphEdgeOut(TransactionEdgeOut):
    in_case: bool


class GraphNodeOut(BaseModel):
    id: str
    type: Literal["account", "beneficiary"]
    label: str
    status: str | None
    is_case_party: bool
    alert_ids: list[str]


class GraphWindow(BaseModel):
    start: datetime
    end: datetime


class CaseGraphParams(BaseModel):
    window_hours: int


class CaseGraphOut(BaseModel):
    case_id: str
    parameters: CaseGraphParams
    window: GraphWindow | None  # None when the case has no transactions
    truncated: bool
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]
