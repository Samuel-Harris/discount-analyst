from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from discount_analyst.config.ai_models_config import ModelName


class DashboardSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DASHBOARD_", env_file=".env", extra="ignore"
    )

    database_path: Path = Field(default=Path("data/dashboard.sqlite"))
    default_model: ModelName = Field(default=ModelName.GPT_5_1)
    risk_free_rate: float = Field(default=0.037, ge=0.0, le=0.15)
    use_perplexity: bool = False
    use_mcp_financial_data: bool = True
    is_existing_position: bool = False
