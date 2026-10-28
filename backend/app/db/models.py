"""Import every model module so Base.metadata is complete (used by Alembic)."""

from app.modules.audit import models as audit_models
from app.modules.cases import models as case_models
from app.modules.copilot import models as copilot_models
from app.modules.evidence import models as evidence_models
from app.modules.notes import models as note_models
from app.modules.parties import models as party_models
from app.modules.transactions import models as transaction_models
from app.modules.users import models as user_models

__all__ = [
    "audit_models",
    "case_models",
    "copilot_models",
    "evidence_models",
    "note_models",
    "party_models",
    "transaction_models",
    "user_models",
]
