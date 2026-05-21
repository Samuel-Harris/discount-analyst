"""Tests for deterministic mock rating-table verdict helpers."""

from __future__ import annotations

from backend.dev import mock_outputs


def test_mock_rating_table_decision_has_rule_id() -> None:
    c = mock_outputs.mock_surveyor_candidate(ticker="BETA.L")
    d = mock_outputs.mock_rating_table_decision(c, is_existing_position=False)
    assert d.decision_rule_id == "rating_table_v1"
    assert d.ticker == c.ticker


def test_mock_rating_table_decision_stable_per_ticker() -> None:
    t = "BETA.L"
    c1 = mock_outputs.mock_surveyor_candidate(ticker=t)
    c2 = mock_outputs.mock_surveyor_candidate(ticker=t.casefold())
    a = mock_outputs.mock_rating_table_decision(c1, is_existing_position=False)
    b = mock_outputs.mock_rating_table_decision(c2, is_existing_position=False)
    assert a.rating == b.rating
    assert a.recommended_action == b.recommended_action


def test_mock_rating_table_new_vs_existing_recommended_action_differs() -> None:
    c = mock_outputs.mock_surveyor_candidate(ticker="BETA.L")
    d_new = mock_outputs.mock_rating_table_decision(c, is_existing_position=False)
    d_ex = mock_outputs.mock_rating_table_decision(c, is_existing_position=True)
    assert d_new.rating == d_ex.rating
    assert d_new.recommended_action != d_ex.recommended_action
