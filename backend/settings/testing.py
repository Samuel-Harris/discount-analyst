"""Construct :class:`Settings` with dummy pipeline keys for backend tests."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from discount_analyst.config.ai_models_config import ModelName

from common.config import (
    DashboardLogLevel,
    EODHD,
    FMP,
    Logging,
    Perplexity,
    Settings,
)

LOGFIRE_TOKEN_FOR_TESTS = "pytest-dummy-logfire-token"


def dashboard_settings_for_tests(
    *,
    database_path: Path | None = None,
    logfire_api_key: str = LOGFIRE_TOKEN_FOR_TESTS,
    deploy_env: Literal["DEV", "PROD"] = "PROD",
    log_level: DashboardLogLevel = "INFO",
) -> Settings:
    """Build a valid :class:`Settings` instance without loading ``.env`` files."""
    return Settings(
        perplexity=Perplexity(
            api_key="pytest-perplexity-key", rate_limit_per_minute=60
        ),
        fmp=FMP(api_key="pytest-fmp-key"),
        eodhd=EODHD(api_key="pytest-eodhd-key"),
        anthropic=None,
        openai=None,
        google=None,
        logging=Logging(
            logfire_api_key=logfire_api_key,
            log_level=log_level,
        ),
        database_path=database_path or Path("data/dashboard.sqlite"),
        default_model=ModelName.GPT_5_1,
        risk_free_rate=0.037,
        use_perplexity=False,
        use_mcp_financial_data=True,
        deploy_env=deploy_env,
    )
