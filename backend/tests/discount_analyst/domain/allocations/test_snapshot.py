"""Tests for current-portfolio snapshot validation."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from discount_analyst.domain.allocations.constants import WEIGHT_SUM_TOLERANCE_PP
from discount_analyst.domain.allocations.snapshot import (
    CurrentPortfolioSnapshot,
    CurrentPositionWeight,
    SterlingPortfolioLedger,
    SterlingPosition,
    snapshot_from_sterling_ledger,
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


def test_sterling_ledger_rejects_duplicate_tickers() -> None:
    with pytest.raises(ValidationError, match="unique case-insensitively"):
        SterlingPortfolioLedger(
            positions=(
                SterlingPosition(ticker="Abc.L", value_gbp=Decimal("10")),
                SterlingPosition(ticker="ABC.L", value_gbp=Decimal("10")),
            ),
            cash_gbp=Decimal("0"),
        )


def test_snapshot_from_zero_total_ledger_is_cash_only() -> None:
    snapshot = snapshot_from_sterling_ledger(
        SterlingPortfolioLedger(positions=(), cash_gbp=Decimal("0")),
        as_of=date(2026, 8, 30),
    )

    assert snapshot.positions == ()
    assert snapshot.cash_weight_pct == 100.0


def test_snapshot_from_zero_total_with_holdings_keeps_tickers_at_zero() -> None:
    snapshot = snapshot_from_sterling_ledger(
        SterlingPortfolioLedger(
            positions=(
                SterlingPosition(ticker="ZERO.L", value_gbp=Decimal("0")),
                SterlingPosition(ticker="NIL.L", value_gbp=Decimal("0")),
            ),
            cash_gbp=Decimal("0"),
        ),
        as_of=date(2026, 8, 30),
    )

    assert snapshot.positions[0].ticker == "ZERO.L"
    assert snapshot.positions[0].current_weight_pct == 0.0
    assert snapshot.positions[1].ticker == "NIL.L"
    assert snapshot.positions[1].current_weight_pct == 0.0
    assert snapshot.cash_weight_pct == 100.0
    _assert_weights_total_100(snapshot)


def test_snapshot_from_mixed_positions_and_cash() -> None:
    snapshot = snapshot_from_sterling_ledger(
        SterlingPortfolioLedger(
            positions=(
                SterlingPosition(ticker="ABC.L", value_gbp=Decimal("50.00")),
                SterlingPosition(ticker="XYZ", value_gbp=Decimal("30.00")),
            ),
            cash_gbp=Decimal("20.00"),
        ),
        as_of=date(2026, 8, 30),
    )

    assert snapshot.as_of == date(2026, 8, 30)
    assert snapshot.positions[0].ticker == "ABC.L"
    assert snapshot.positions[0].current_weight_pct == 50.0
    assert snapshot.positions[1].ticker == "XYZ"
    assert snapshot.positions[1].current_weight_pct == 30.0
    assert snapshot.cash_weight_pct == 20.0
    _assert_weights_total_100(snapshot)


def test_snapshot_from_zero_cash_puts_remainder_on_last_holding() -> None:
    snapshot = snapshot_from_sterling_ledger(
        SterlingPortfolioLedger(
            positions=(
                SterlingPosition(ticker="A.L", value_gbp=Decimal("100.00")),
                SterlingPosition(ticker="B.L", value_gbp=Decimal("100.00")),
                SterlingPosition(ticker="C.L", value_gbp=Decimal("100.00")),
            ),
            cash_gbp=Decimal("0"),
        ),
        as_of=date(2026, 8, 30),
    )

    assert snapshot.positions[0].current_weight_pct == 33.33
    assert snapshot.positions[1].current_weight_pct == 33.33
    assert snapshot.positions[2].current_weight_pct == 33.34
    assert snapshot.cash_weight_pct == 0.0
    _assert_weights_total_100(snapshot)


def test_snapshot_from_ledger_keeps_zero_value_holding_at_zero() -> None:
    snapshot = snapshot_from_sterling_ledger(
        SterlingPortfolioLedger(
            positions=(
                SterlingPosition(ticker="ABC.L", value_gbp=Decimal("80.00")),
                SterlingPosition(ticker="ZERO.L", value_gbp=Decimal("0")),
            ),
            cash_gbp=Decimal("20.00"),
        ),
        as_of=date(2026, 8, 30),
    )

    assert snapshot_weight_for_ticker(snapshot, "ZERO.L") == 0.0
    assert snapshot.cash_weight_pct == 20.0
    _assert_weights_total_100(snapshot)


def _assert_weights_total_100(snapshot: CurrentPortfolioSnapshot) -> None:
    total = sum(position.current_weight_pct for position in snapshot.positions)
    total += snapshot.cash_weight_pct
    assert abs(total - 100.0) <= WEIGHT_SUM_TOLERANCE_PP
