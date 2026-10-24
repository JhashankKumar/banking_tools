"""User management use cases. Only Supervisors reach these (checked by the router)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.pagination import PageParams
from app.core.errors import AppError
from app.core.security import hash_password
from app.modules.audit import service as audit
from app.modules.audit.models import Outcome
from app.modules.users.models import Role, User
from app.modules.users.schemas import UserCreate, UserUpdate


class DuplicateUsernameError(AppError):
    status = 409
    code = "USER_USERNAME_TAKEN"
    message = "Username already exists"


class UserNotFoundError(AppError):
    status = 404
    code = "USER_NOT_FOUND"
    message = "User not found"


class SelfLockoutError(AppError):
    status = 409
    code = "USER_SELF_LOCKOUT"
    message = "Supervisors cannot deactivate or change the role of their own account"


def list_users(session: Session, page: PageParams) -> tuple[list[User], int]:
    total = session.scalar(select(func.count()).select_from(User)) or 0
    users = session.scalars(
        select(User).order_by(User.username).limit(page.limit).offset(page.offset)
    ).all()
    return list(users), total


def create_user(session: Session, *, actor: User, data: UserCreate, request_id: str | None) -> User:
    if session.scalar(select(User.id).where(User.username == data.username)) is not None:
        raise DuplicateUsernameError
    user = User(username=data.username, password_hash=hash_password(data.password), role=data.role)
    session.add(user)
    try:
        session.flush()
    except IntegrityError as error:  # Concurrent create of the same username.
        raise DuplicateUsernameError from error
    audit.record(
        session,
        action="user.created",
        outcome=Outcome.SUCCESS,
        actor_user_id=actor.id,
        request_id=request_id,
        resource_type="user",
        resource_id=str(user.id),
        details={"role": user.role.value},
    )
    return user


def update_user(
    session: Session, *, actor: User, user_id: uuid.UUID, data: UserUpdate, request_id: str | None
) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise UserNotFoundError
    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    is_self = user.id == actor.id
    demotes_self = "role" in changes and changes["role"] != Role.SUPERVISOR
    deactivates_self = changes.get("is_active") is False
    if is_self and (demotes_self or deactivates_self):
        raise SelfLockoutError

    if "role" in changes:
        user.role = changes["role"]
    if "is_active" in changes:
        user.is_active = changes["is_active"]
    if "password" in changes:
        user.password_hash = hash_password(changes["password"])
    session.flush()
    session.refresh(user)
    audit.record(
        session,
        action="user.updated",
        outcome=Outcome.SUCCESS,
        actor_user_id=actor.id,
        request_id=request_id,
        resource_type="user",
        resource_id=str(user.id),
        details={"fields": ",".join(sorted(changes))},  # Names only, never values.
    )
    return user
