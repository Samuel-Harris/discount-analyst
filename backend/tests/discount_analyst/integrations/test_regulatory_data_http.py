from pathlib import Path

import pytest

from discount_analyst.agents.tools.regulatory_data.errors import (
    REFRESH_COMMAND,
    ColdCacheError,
    SecUserAgentMissingError,
)
from discount_analyst.agents.tools.regulatory_data import http as regulatory_http
from discount_analyst.agents.tools.regulatory_data.http import (
    METADATA_TIMEOUT_SECONDS,
    create_metadata_client,
    sec_request_headers,
)
from discount_analyst.config.testing_settings import dashboard_settings_for_tests


def test_metadata_client_timeout_is_thirty_seconds() -> None:
    client = create_metadata_client()
    assert METADATA_TIMEOUT_SECONDS == 30.0
    assert client.timeout.read == 30.0
    assert client.timeout.connect == 30.0


def test_sec_headers_require_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        regulatory_http,
        "app_settings",
        dashboard_settings_for_tests(sec_user_agent="  "),
    )
    with pytest.raises(SecUserAgentMissingError, match="SEC__USER_AGENT"):
        sec_request_headers()


def test_sec_headers_include_required_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        regulatory_http,
        "app_settings",
        dashboard_settings_for_tests(
            sec_user_agent="DiscountAnalyst/0.1 (analyst@example.com)"
        ),
    )
    headers = sec_request_headers()
    assert headers["User-Agent"] == "DiscountAnalyst/0.1 (analyst@example.com)"
    assert "gzip" in headers["Accept-Encoding"]


def test_cold_cache_error_names_refresh_command() -> None:
    error = ColdCacheError("SEC companyfacts", refresh_flags="--sec")
    assert REFRESH_COMMAND in str(error)
    assert "--sec" in str(error)


def test_settings_defaults_for_regulatory_cache(tmp_path: Path) -> None:
    settings = dashboard_settings_for_tests(
        regulatory_data_cache_dir=tmp_path / "reg",
        sec_user_agent="",
    )
    assert settings.regulatory_data_cache_dir == tmp_path / "reg"
    assert settings.sec_user_agent == ""
