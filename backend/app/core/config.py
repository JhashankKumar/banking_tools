from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# One .env at the repository root is shared by docker compose and the backend.
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


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

    # AI copilot (docs/specs/2026-10-24-milestone-5-ai-copilot-design.md). The OpenRouter names
    # are documented without the OFI_ prefix; the prefixed form is accepted too.
    openrouter_api_key: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("OPENROUTER_API_KEY", "OFI_OPENROUTER_API_KEY")
    )
    openrouter_model: str = Field(
        default="openai/gpt-oss-120b",
        validation_alias=AliasChoices("OPENROUTER_MODEL", "OFI_OPENROUTER_MODEL"),
    )
    copilot_daily_budget_usd: Decimal = Field(default=Decimal("2.00"), ge=0)
    copilot_questions_per_hour: int = Field(default=20, ge=1)
    copilot_max_tool_calls: int = Field(default=6, ge=1, le=20)
    copilot_max_model_turns: int = Field(default=8, ge=2, le=20)
    copilot_history_messages: int = Field(default=10, ge=0, le=50)
    # Used only when the provider does not report a cost for a call.
    copilot_fallback_cost_per_1k_tokens: Decimal = Field(default=Decimal("0.002"), ge=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]  (required fields come from the environment)
