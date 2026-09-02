"""Unified :class:`Settings` validation (e.g. mandatory Logfire API key)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from discount_analyst.config.settings import AgentDefaultModels, Settings
from discount_analyst.config.testing_settings import dashboard_settings_for_tests
from discount_analyst.domain.model_selection.model_name import ModelName


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


def test_agent_default_models_baked_in_defaults() -> None:
    defaults = AgentDefaultModels()
    assert defaults.surveyor is ModelName.GPT_5_6_LUNA
    assert defaults.profiler is ModelName.GPT_5_6_LUNA
    assert defaults.researcher is ModelName.GPT_5_6_LUNA
    assert defaults.strategist is ModelName.GPT_5_6_LUNA
    assert defaults.sentinel is ModelName.GPT_5_6_LUNA
    assert defaults.appraiser is ModelName.GPT_5_6_LUNA
    assert defaults.curator is ModelName.GPT_5_6_TERRA


def test_agent_default_models_curator_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENT_DEFAULT_MODELS__CURATOR", "gpt-5.1")
    dummy = dashboard_settings_for_tests()
    loaded = Settings(
        perplexity=dummy.perplexity,
        fmp=dummy.fmp,
        eodhd=dummy.eodhd,
        logging=dummy.logging,
        _env_file=None,
    )
    assert loaded.agent_default_models.curator is ModelName.GPT_5_1
    assert loaded.agent_default_models.surveyor is ModelName.GPT_5_6_LUNA
