"""Tests for financial MCP server factory wiring."""

from __future__ import annotations

import pytest

import discount_analyst.integrations.financial_data_mcp as financial_data_mcp


def test_create_financial_data_mcp_servers_includes_eodhd_when_not_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    eodhd = financial_data_mcp.settings.eodhd.model_copy(update={"disabled": False})
    monkeypatch.setattr(financial_data_mcp.settings, "eodhd", eodhd)
    servers = financial_data_mcp.create_financial_data_mcp_servers()
    assert len(servers) == 2
    assert servers[0].id == "eodhd"
    assert servers[1].id == "fmp"


def test_create_financial_data_mcp_servers_omits_eodhd_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    eodhd = financial_data_mcp.settings.eodhd.model_copy(update={"disabled": True})
    monkeypatch.setattr(financial_data_mcp.settings, "eodhd", eodhd)
    servers = financial_data_mcp.create_financial_data_mcp_servers()
    assert len(servers) == 1
    assert servers[0].id == "fmp"
