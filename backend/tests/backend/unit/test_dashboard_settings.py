"""Unified :class:`Settings` validation (e.g. mandatory Logfire API key)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from discount_analyst.config.settings import Settings
from discount_analyst.config.testing_settings import dashboard_settings_for_tests


def test_logfire_api_key_rejects_whitespace_only() -> None:
    with pytest.raises(ValidationError, match="LOGGING__LOGFIRE_API_KEY"):
        dashboard_settings_for_tests(logfire_api_key="   ")


def test_regulatory_data_settings_defaults() -> None:
    settings = dashboard_settings_for_tests()
    assert settings.regulatory_data_cache_dir.as_posix() == "data/regulatory_data"
    assert settings.sec_user_agent == ""


def test_regulatory_data_settings_read_canonical_env_names(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache_dir = tmp_path / "regulatory_data"
    monkeypatch.setenv("REGULATORY_DATA_CACHE_DIR", str(cache_dir))
    monkeypatch.setenv("SEC__USER_AGENT", "DiscountAnalyst/0.1 (analyst@example.com)")
    dummy = dashboard_settings_for_tests()
    loaded = Settings(
        perplexity=dummy.perplexity,
        fmp=dummy.fmp,
        eodhd=dummy.eodhd,
        logging=dummy.logging,
    )
    assert loaded.regulatory_data_cache_dir == cache_dir
    assert loaded.sec_user_agent == "DiscountAnalyst/0.1 (analyst@example.com)"
