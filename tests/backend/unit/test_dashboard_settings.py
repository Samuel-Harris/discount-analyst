"""Unified :class:`Settings` validation (e.g. mandatory Logfire API key)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.settings.testing import dashboard_settings_for_tests


def test_logfire_api_key_rejects_whitespace_only() -> None:
    with pytest.raises(ValidationError, match="LOGGING__LOGFIRE_API_KEY"):
        dashboard_settings_for_tests(logfire_api_key="   ")
