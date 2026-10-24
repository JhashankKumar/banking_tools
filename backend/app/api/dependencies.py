"""Request-scoped dependencies: database session, current user, and permission checks."""

import logging
from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.errors import ForbiddenError, NotAuthenticatedError
from app.core.permissions import Permission, has_permission
from app.core.security import decode_access_token
from app.db.session import get_session
from app.modules.audit import service as audit
from app.modules.audit.models import Outcome
from app.modules.users.models import User

# scope="function": the commit in get_session runs before the response is sent, so a failed
# commit becomes a 500 instead of a success whose writes (including audit rows) were lost.
DbSession = Annotated[Session, Depends(get_session, scope="function")]

_bearer = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
logger = logging.getLogger(__name__)


def request_id_of(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def get_current_user(session: DbSession, token: Annotated[str | None, Depends(_bearer)]) -> User:
    """The active user named by the bearer token, re-read from the database on every request."""
    if token is None:
        raise NotAuthenticatedError
    try:
        user_id = decode_access_token(token)
    except jwt.InvalidTokenError as error:
        # Reason only (e.g. ExpiredSignatureError); never log the token itself.
        logger.info("Rejected access token: %s", type(error).__name__)
        raise NotAuthenticatedError from None
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise NotAuthenticatedError
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require(permission: Permission) -> Callable[..., User]:
    """Dependency factory: the current user, or 403 (audited) if their role lacks `permission`."""

    def dependency(user: CurrentUser, session: DbSession, request: Request) -> User:
        if not has_permission(user.role, permission):
            audit.record(
                session,
                action="access.denied",
                outcome=Outcome.DENIED,
                actor_user_id=user.id,
                request_id=request_id_of(request),
                resource_type="endpoint",
                resource_id=request.url.path,
                details={"permission": permission.value},
            )
            session.commit()  # Keep the audit row even though the request is about to fail.
            raise ForbiddenError
        return user

    return dependency
