"""Tests for financial MCP server factory wiring."""

from __future__ import annotations

import pytest


@pytest.fixture()
def financial_data_mcp_module():
    import discount_analyst.integrations.financial_data_mcp as m

    return m


def test_create_financial_data_mcp_servers_includes_eodhd_when_not_disabled(
    monkeypatch: pytest.MonkeyPatch,
    financial_data_mcp_module,
) -> None:
    m = financial_data_mcp_module
    eodhd = m.settings.eodhd.model_copy(update={"disabled": False})
    monkeypatch.setattr(m.settings, "eodhd", eodhd)
    servers = m.create_financial_data_mcp_servers()
    assert len(servers) == 2
    assert servers[0].tool_prefix == "eodhd"
    assert servers[1].tool_prefix == "fmp"


def test_create_financial_data_mcp_servers_omits_eodhd_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
    financial_data_mcp_module,
) -> None:
    m = financial_data_mcp_module
    eodhd = m.settings.eodhd.model_copy(update={"disabled": True})
    monkeypatch.setattr(m.settings, "eodhd", eodhd)
    servers = m.create_financial_data_mcp_servers()
    assert len(servers) == 1
    assert servers[0].tool_prefix == "fmp"
