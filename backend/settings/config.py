from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from discount_analyst.config.ai_models_config import ModelName

DashboardLogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class DashboardSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DASHBOARD_", env_file=".env", extra="ignore"
    )

    database_path: Path = Field(default=Path("data/dashboard.sqlite"))
    default_model: ModelName = Field(default=ModelName.GPT_5_1)
    risk_free_rate: float = Field(default=0.037, ge=0.0, le=0.15)
    use_perplexity: bool = False
    use_mcp_financial_data: bool = True
    deploy_env: Literal["DEV", "PROD"] = Field(
        default="DEV",
        validation_alias=AliasChoices("ENV"),
        description="Build/runtime ENV (matches frontend / Compose web build args).",
    )
    log_level: DashboardLogLevel = Field(
        default="INFO",
        description="Minimum Logfire console level for the dashboard API process.",
    )
    logfire_token: SecretStr = Field(
        description="Logfire ingest token (required); set DASHBOARD_LOGFIRE_TOKEN.",
    )

    @field_validator("logfire_token", mode="after")
    @classmethod
    def _logfire_token_non_empty(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value().strip():
            msg = "DASHBOARD_LOGFIRE_TOKEN must be set to a non-empty value"
            raise ValueError(msg)
        return v
