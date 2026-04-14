"""Dashboard Logfire bootstrap (no dependency on discount_analyst nested .env)."""

from __future__ import annotations

import logfire
from fastapi import FastAPI
from logfire import ConsoleOptions, LevelName

from backend.settings.config import DashboardLogLevel, DashboardSettings

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
    settings: DashboardSettings, app: FastAPI | None = None
) -> None:
    """Configure Logfire once; optionally instrument a FastAPI app (per app instance)."""
    global _configured

    if not _configured:
        token: str | None = None
        if settings.logfire_token is not None:
            token = settings.logfire_token.get_secret_value()
            if token == "":
                token = None

        send_to_logfire = bool(token)
        level = _LEVEL_MAP[settings.log_level]
        logfire.configure(
            service_name="discount-analyst-dashboard",
            environment=settings.deploy_env.lower(),
            send_to_logfire=send_to_logfire,
            token=token,
            console=ConsoleOptions(min_log_level=level),
            min_level=level,
            inspect_arguments=False,
        )
        _configured = True

    if app is not None:
        app_id = id(app)
        if app_id not in _instrumented_app_ids:
            logfire.instrument_fastapi(app)
            _instrumented_app_ids.add(app_id)
