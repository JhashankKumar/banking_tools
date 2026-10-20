from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# One .env at the repository root is shared by docker compose and the backend.
ENV_FILE = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    """Typed application settings, read from OFI_* environment variables or the repo-root .env.

    Environment variables take precedence over the .env file.
    """

    model_config = SettingsConfigDict(env_prefix="OFI_", env_file=ENV_FILE, extra="ignore")

    app_name: str = "OpenFraud Investigator API"
    app_env: Literal["local", "test", "ci", "production"] = "local"
    docs_enabled: bool = False  # Interactive API docs and OpenAPI schema; opt in for local dev.
    database_url: str
    jwt_secret: SecretStr = Field(min_length=32)
    access_token_minutes: int = Field(default=30, ge=1, le=120)
    demo_password: SecretStr | None = None  # Only used by `python -m app.seed`.


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]  (required fields come from the environment)
