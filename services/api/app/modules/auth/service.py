from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import burn_password_check, verify_password
from app.modules.users.models import User


def authenticate(session: Session, username: str, password: str) -> User | None:
    """The active user with these credentials, or None. Unknown users cost the same time."""
    user = session.scalars(select(User).where(User.username == username)).one_or_none()
    if user is None:
        burn_password_check(password)
        return None
    if not verify_password(password, user.password_hash) or not user.is_active:
        return None
    return user
