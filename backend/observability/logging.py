"""Dashboard Logfire bootstrap using unified :class:`Settings`."""

from __future__ import annotations

import logfire
from fastapi import FastAPI
from logfire import ConsoleOptions, LevelName

from discount_analyst.agents.common.ai_logging import AI_LOGFIRE
from backend.settings.config import DashboardLogLevel, Settings

_configured = False
_instrumented_app_ids: set[int] = set()

_LEVEL_MAP: dict[DashboardLogLevel, LevelName] = {
    "DEBUG": "debug",
    "INFO": "info",
    "WARNING": "warning",
    "ERROR": "error",
    "CRITICAL": "fatal",
}


def configure_dashboard_observability(
    settings: Settings, app: FastAPI | None = None
) -> None:
    """Configure Logfire once; optionally instrument a FastAPI app (per app instance)."""
    global _configured

    if not _configured:
        token = settings.logging.logfire_api_key
        level = _LEVEL_MAP[settings.logging.log_level]
        logfire.configure(
            service_name="discount-analyst-dashboard",
            environment=settings.deploy_env.lower(),
            send_to_logfire=True,
            token=token,
            console=ConsoleOptions(min_log_level=level),
            min_level=level,
            inspect_arguments=False,
        )
        # Instrument pydantic-ai via the AI-tagged logger while preserving plain dashboard logs.
        AI_LOGFIRE.instrument_pydantic_ai()
        logfire.instrument_httpx(capture_all=True)
        _configured = True

    if app is not None:
        app_id = id(app)
        if app_id not in _instrumented_app_ids:
            logfire.instrument_fastapi(app)
            _instrumented_app_ids.add(app_id)
