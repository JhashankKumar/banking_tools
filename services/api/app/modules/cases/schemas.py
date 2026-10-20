from datetime import datetime

from pydantic import BaseModel

from app.modules.cases.models import CaseStatus


class CaseOut(BaseModel):
    id: str
    title: str
    status: CaseStatus
    opened_at: datetime
    alert_ids: list[str]
    transaction_count: int
    is_synthetic: bool
