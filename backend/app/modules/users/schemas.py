import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.modules.users.models import Role

Username = Annotated[str, Field(pattern=r"^[a-z0-9_.-]{3,32}$")]
Password = Annotated[str, Field(min_length=12, max_length=128)]


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: Username
    password: Password
    role: Role


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role | None = None
    is_active: bool | None = None
    password: Password | None = None


class UserOut(BaseModel):
    """Public view of a user. Never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime
