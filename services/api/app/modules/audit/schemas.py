import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.audit.models import Outcome


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    occurred_at: datetime
    actor_user_id: uuid.UUID | None
    action: str
    resource_type: str | None
    resource_id: str | None
    outcome: Outcome
    request_id: str | None
    details: dict[str, str]
