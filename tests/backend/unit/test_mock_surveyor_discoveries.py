"""Tests for mock Surveyor discovery helpers."""

from __future__ import annotations

from backend.dev import mock_outputs


def test_dashboard_discoveries_excludes_portfolio_and_caps() -> None:
    out = mock_outputs.mock_surveyor_dashboard_discoveries({"META"}, limit=2)
    assert len(out.candidates) == 2
    tickers = {c.ticker.casefold() for c in out.candidates}
    assert "meta" not in tickers
    assert tickers == {"disc.l", "alph.l"}


def test_dashboard_discoveries_empty_when_defaults_all_in_portfolio() -> None:
    full = mock_outputs.mock_surveyor_output()
    fold = {c.ticker.casefold() for c in full.candidates}
    out = mock_outputs.mock_surveyor_dashboard_discoveries(fold, limit=3)
    assert out.candidates == []


def test_mock_sentinel_lane_gate_is_mixed_for_default_dashboard_discoveries() -> None:
    """First three default discoveries must not all share the same mock Sentinel fate."""
    out = mock_outputs.mock_surveyor_dashboard_discoveries(set(), limit=3)
    flags = [
        mock_outputs.mock_sentinel_proceed_for_dashboard_lane(c.ticker)
        for c in out.candidates
    ]
    assert len(flags) == 3
    assert any(flags) and not all(flags)


def test_mock_sentinel_lane_gate_is_stable_per_ticker() -> None:
    t = "BETA.L"
    a = mock_outputs.mock_sentinel_proceed_for_dashboard_lane(t)
    b = mock_outputs.mock_sentinel_proceed_for_dashboard_lane(t.casefold())
    assert a is b is True
