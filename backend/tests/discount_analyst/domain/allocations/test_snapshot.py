"""Tests for current-portfolio snapshot validation."""

from datetime import date

import pytest
from pydantic import ValidationError

from discount_analyst.domain.allocations.snapshot import (
    CurrentPortfolioSnapshot,
    CurrentPositionWeight,
    snapshot_weight_for_ticker,
)


def test_snapshot_accepts_weights_totalling_100() -> None:
    snapshot = CurrentPortfolioSnapshot(
        as_of=date(2026, 8, 30),
        positions=(
            CurrentPositionWeight(ticker="ABC.L", current_weight_pct=40.0),
            CurrentPositionWeight(ticker="XYZ", current_weight_pct=25.0),
        ),
        cash_weight_pct=35.0,
    )

    assert snapshot_weight_for_ticker(snapshot, "abc.l") == 40.0
    assert snapshot_weight_for_ticker(snapshot, "missing") is None


def test_snapshot_accepts_cash_only() -> None:
    snapshot = CurrentPortfolioSnapshot(
        as_of=date(2026, 8, 30),
        positions=(),
        cash_weight_pct=100.0,
    )

    assert snapshot.cash_weight_pct == 100.0


def test_snapshot_rejects_duplicate_tickers() -> None:
    with pytest.raises(ValidationError, match="unique case-insensitively"):
        CurrentPortfolioSnapshot(
            as_of=date(2026, 8, 30),
            positions=(
                CurrentPositionWeight(ticker="Abc.L", current_weight_pct=50.0),
                CurrentPositionWeight(ticker="ABC.L", current_weight_pct=50.0),
            ),
            cash_weight_pct=0.0,
        )


def test_snapshot_rejects_weights_not_totalling_100() -> None:
    with pytest.raises(ValidationError, match="total 100%"):
        CurrentPortfolioSnapshot(
            as_of=date(2026, 8, 30),
            positions=(CurrentPositionWeight(ticker="ABC.L", current_weight_pct=40.0),),
            cash_weight_pct=40.0,
        )
