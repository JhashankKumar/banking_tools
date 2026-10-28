from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import require
from app.api.responses import DataResponse
from app.core.permissions import Permission
from app.modules.detection.registry import RULES
from app.modules.users.models import User

router = APIRouter(prefix="/rules", tags=["rules"])


class RuleOut(BaseModel):
    id: str
    version: str
    code: str
    title: str
    description: str
    required_fields: list[str]
    false_positive_caveats: list[str]
    parameters: dict[str, str]


@router.get("")
def list_rules(
    _user: Annotated[User, Depends(require(Permission.ALERT_READ))],
) -> DataResponse[list[RuleOut]]:
    """The registered rule catalog. Small and fixed, so not paginated."""
    return DataResponse(
        data=[
            RuleOut(
                id=rule.rule_id,
                version=rule.version,
                code=rule.code,
                title=rule.title,
                description=rule.description,
                required_fields=list(rule.required_fields),
                false_positive_caveats=list(rule.false_positive_caveats),
                parameters=dict(rule.parameters),
            )
            for rule in RULES
        ]
    )
