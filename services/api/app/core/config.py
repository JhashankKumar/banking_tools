from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings, read from OFI_* environment variables or a local .env."""

    model_config = SettingsConfigDict(env_prefix="OFI_", env_file=".env", extra="ignore")

    app_name: str = "OpenFraud Investigator API"
    app_env: Literal["local", "test", "ci", "production"] = "local"
    docs_enabled: bool = False  # Interactive API docs and OpenAPI schema; opt in for local dev.


@lru_cache
def get_settings() -> Settings:
    return Settings()
