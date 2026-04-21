"""Re-exports unified :class:`Settings` from ``discount_analyst.config.settings``."""

from discount_analyst.config.settings import (
    DashboardLogLevel,
    Logging,
    Settings,
    load_settings,
)

DashboardSettings = Settings
load_dashboard_settings = load_settings

__all__ = [
    "DashboardLogLevel",
    "DashboardSettings",
    "Logging",
    "Settings",
    "load_dashboard_settings",
    "load_settings",
]
