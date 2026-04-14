from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
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
    logfire_token: SecretStr | None = Field(
        default=None,
        description="Optional Logfire ingest token; when unset, logs stay console-only.",
    )
