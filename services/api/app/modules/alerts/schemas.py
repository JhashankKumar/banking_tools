from datetime import datetime

from pydantic import BaseModel

from app.modules.transactions.schemas import PartyRef


class RuleRef(BaseModel):
    id: str
    version: str
    title: str


class AlertOut(BaseModel):
    id: str
    rule: RuleRef
    entity: PartyRef
    trigger_transaction_id: str
    transaction_ids: list[str]
    case_id: str | None
    triggered_at: datetime
    explanation: str
    metrics: dict[str, str]
    is_synthetic: bool
