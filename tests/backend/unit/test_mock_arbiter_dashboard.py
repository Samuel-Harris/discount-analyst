"""Tests for deterministic mock Arbiter verdict helpers."""

from __future__ import annotations

from backend.dev import mock_outputs


def test_mock_arbiter_ratings_vary_across_default_discovery_tickers() -> None:
    out = mock_outputs.mock_surveyor_dashboard_discoveries(set(), limit=3)
    ratings = {
        mock_outputs.mock_arbiter_rating_for_dashboard_lane(c.ticker)
        for c in out.candidates
    }
    assert len(ratings) >= 2


def test_mock_arbiter_rating_stable_per_ticker() -> None:
    t = "BETA.L"
    a = mock_outputs.mock_arbiter_rating_for_dashboard_lane(t)
    b = mock_outputs.mock_arbiter_rating_for_dashboard_lane(t.casefold())
    assert a is b


def test_mock_arbiter_decision_uses_dashboard_rating() -> None:
    c = mock_outputs.mock_surveyor_candidate(ticker="BETA.L")
    d = mock_outputs.mock_arbiter_decision(c, is_existing_position=False)
    assert d.rating == mock_outputs.mock_arbiter_rating_for_dashboard_lane("BETA.L")
