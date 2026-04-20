"""``DashboardSettings`` validation (e.g. mandatory Logfire token)."""

from __future__ import annotations

import pytest
from pydantic import SecretStr, ValidationError

from backend.settings.config import DashboardSettings


def test_logfire_token_rejects_whitespace_only() -> None:
    with pytest.raises(ValidationError, match="DASHBOARD_LOGFIRE_TOKEN"):
        DashboardSettings(logfire_token=SecretStr("   "))
