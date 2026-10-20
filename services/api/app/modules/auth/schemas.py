import uuid

from pydantic import BaseModel

from app.modules.users.models import Role


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105  (OAuth2 token type, not a secret)
    expires_in: int


class MeOut(BaseModel):
    id: uuid.UUID
    username: str
    role: Role
    permissions: list[str]
