from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import Connection

from app.api.dependencies import Audit, require
from app.api.responses import DataResponse
from app.core.config import get_settings
from app.core.permissions import Permission
from app.db.session import get_engine
from app.modules.safety.registry import CATALOGUE
from app.modules.safety.runner import run_catalogue
from app.modules.safety.schemas import SafetyCheckOut, SafetyRunOut
from app.modules.users.models import User

router = APIRouter(prefix="/safety", tags=["safety"])
SafetyRunner = Annotated[User, Depends(require(Permission.SAFETY_RUN))]


def get_safety_connection() -> Iterator[Connection]:
    """A connection of its own: the run's transaction is rolled back, the request's is not."""
    with get_engine().connect() as connection:
        yield connection


SafetyConnection = Annotated[Connection, Depends(get_safety_connection)]


@router.get("/checks")
def list_checks(_user: SafetyRunner) -> DataResponse[list[SafetyCheckOut]]:
    return DataResponse(
        data=[
            SafetyCheckOut(id=c.id, category=c.category, attack=c.attack, defence=c.defence)
            for c in CATALOGUE
        ]
    )


@router.post("/runs")
def run_checks(
    _user: SafetyRunner, connection: SafetyConnection, trail: Audit
) -> DataResponse[SafetyRunOut]:
    result = run_catalogue(connection, get_settings())
    trail.success(
        "safety.checks.run",
        resource_type="safety",
        details={k: str(v) for k, v in result.counts.model_dump().items()},
    )
    return DataResponse(data=result)
