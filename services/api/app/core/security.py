"""Password hashing and access tokens. No other module touches pwdlib or PyJWT directly."""

import uuid
from datetime import datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

_ALGORITHM = "HS256"
_password_hash = PasswordHash.recommended()  # Argon2id
# Verified against when the username is unknown, so response time doesn't reveal which users exist.
_DUMMY_HASH = _password_hash.hash("dummy-password-for-timing-only")


def hash_password(plain: str) -> str:
    return _password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _password_hash.verify(plain, hashed)


def burn_password_check(plain: str) -> None:
    """Spend the same effort as a real check when no user matched."""
    _password_hash.verify(plain, _DUMMY_HASH)


def create_access_token(user_id: uuid.UUID, now: datetime) -> str:
    settings = get_settings()
    claims = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    secret = settings.jwt_secret.get_secret_value()
    return jwt.encode(claims, secret, algorithm=_ALGORITHM)  # pyright: ignore[reportUnknownMemberType]


def decode_access_token(token: str) -> uuid.UUID:
    """Return the user ID in a valid, unexpired token. Raises jwt.InvalidTokenError otherwise."""
    claims: dict[str, object] = jwt.decode(  # pyright: ignore[reportUnknownMemberType]
        token,
        get_settings().jwt_secret.get_secret_value(),
        algorithms=[_ALGORITHM],
        options={"require": ["sub", "iat", "exp"]},
    )
    try:
        return uuid.UUID(str(claims["sub"]))
    except ValueError as error:
        raise jwt.InvalidTokenError("subject is not a user id") from error
