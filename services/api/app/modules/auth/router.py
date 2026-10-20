from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import CurrentUser, DbSession, request_id_of
from app.api.responses import DataResponse
from app.core.config import get_settings
from app.core.errors import InvalidCredentialsError
from app.core.permissions import ROLE_PERMISSIONS
from app.core.security import create_access_token
from app.modules.audit import service as audit
from app.modules.audit.models import Outcome
from app.modules.auth.schemas import MeOut, TokenOut
from app.modules.auth.service import authenticate

router = APIRouter(prefix="/auth", tags=["auth"])


# OAuth2 token response (RFC 6749) is a documented exception to the data envelope.
@router.post("/token")
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], session: DbSession, request: Request
) -> TokenOut:
    user = authenticate(session, form.username, form.password)
    if user is None:
        audit.record(
            session,
            action="auth.login.failed",
            outcome=Outcome.FAILURE,
            actor_user_id=None,
            request_id=request_id_of(request),
        )
        session.commit()  # Keep the audit row even though the request is about to fail.
        raise InvalidCredentialsError
    audit.record(
        session,
        action="auth.login.succeeded",
        outcome=Outcome.SUCCESS,
        actor_user_id=user.id,
        request_id=request_id_of(request),
    )
    token = create_access_token(user.id, now=datetime.now(UTC))
    return TokenOut(access_token=token, expires_in=get_settings().access_token_minutes * 60)


@router.get("/me")
def me(user: CurrentUser) -> DataResponse[MeOut]:
    permissions = sorted(p.value for p in ROLE_PERMISSIONS[user.role])
    return DataResponse(
        data=MeOut(id=user.id, username=user.username, role=user.role, permissions=permissions)
    )
