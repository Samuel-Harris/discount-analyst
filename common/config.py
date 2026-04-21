from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from discount_analyst.config.ai_models_config import ModelName

DashboardLogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Perplexity(BaseModel):
    api_key: str
    rate_limit_per_minute: int


class Anthropic(BaseModel):
    api_key: str


class OpenAI(BaseModel):
    api_key: str


class Google(BaseModel):
    api_key: str


class FMP(BaseModel):
    api_key: str


class EODHD(BaseModel):
    api_key: str
    disabled: bool = Field(
        default=False,
        description=(
            "When true, the EODHD MCP server is not registered; FMP MCP is unchanged."
        ),
    )


class Logging(BaseModel):
    """Logfire ingest key and process log levels (dashboard console, CLI scripts, etc.)."""

    logfire_api_key: str = Field(
        description="Logfire ingest token (non-empty); used by the dashboard API and setup helpers.",
    )

    @field_validator("logfire_api_key", mode="after")
    @classmethod
    def _logfire_api_key_non_empty(cls, v: str) -> str:
        if not v.strip():
            msg = "LOGGING__LOGFIRE_API_KEY must be set to a non-empty value"
            raise ValueError(msg)
        return v

    log_level: DashboardLogLevel = Field(
        default="INFO",
        description="Minimum Logfire console level for the dashboard API process.",
    )


_REPO_ROOT = Path(__file__).resolve().parent.parent
_DISCOUNT_ANALYST_DIR = _REPO_ROOT / "discount_analyst"


class Settings(BaseSettings):
    """Unified application settings (pipeline agents, dashboard API, observability)."""

    model_config = SettingsConfigDict(
        env_file=(_DISCOUNT_ANALYST_DIR / ".env", _REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        # Allow ``Settings(database_path=...)`` alongside env aliases like ``DASHBOARD_DATABASE_PATH``.
        populate_by_name=True,
    )

    perplexity: Perplexity
    anthropic: Anthropic | None = None
    openai: OpenAI | None = None
    google: Google | None = None
    fmp: FMP
    eodhd: EODHD
    logging: Logging

    database_path: Path = Field(
        default=Path("data/dashboard.sqlite"),
        validation_alias=AliasChoices("DASHBOARD_DATABASE_PATH", "DATABASE_PATH"),
    )
    default_model: ModelName = Field(
        default=ModelName.GPT_5_1,
        validation_alias=AliasChoices("DASHBOARD_DEFAULT_MODEL"),
    )
    risk_free_rate: float = Field(
        default=0.037,
        ge=0.0,
        le=0.15,
        validation_alias=AliasChoices("DASHBOARD_RISK_FREE_RATE"),
    )
    use_perplexity: bool = Field(
        default=False,
        validation_alias=AliasChoices("DASHBOARD_USE_PERPLEXITY"),
    )
    use_mcp_financial_data: bool = Field(
        default=True,
        validation_alias=AliasChoices("DASHBOARD_USE_MCP_FINANCIAL_DATA"),
    )
    deploy_env: Literal["DEV", "PROD"] = Field(
        default="DEV",
        validation_alias=AliasChoices("ENV", "DASHBOARD_DEPLOY_ENV"),
        description=(
            "Build/runtime deploy environment (matches frontend / Compose web build args)."
        ),
    )


def load_settings() -> Settings:
    """Load settings from the process environment and optional ``.env`` files."""
    return Settings()  # type: ignore[call-arg]


settings = Settings()  # type: ignore[call-arg]
