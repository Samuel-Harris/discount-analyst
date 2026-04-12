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
