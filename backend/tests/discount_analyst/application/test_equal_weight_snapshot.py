"""Equal-weight existing-position snapshot used by mock dashboard Allocator runs."""

from datetime import date

from discount_analyst.adapters.simulation.equal_weight_snapshot import (
    equal_weight_existing_snapshot,
)


def test_empty_existing_tickers_are_cash_only() -> None:
    snapshot = equal_weight_existing_snapshot((), as_of=date(2026, 8, 30))
    assert snapshot.positions == ()
    assert snapshot.cash_weight_pct == 100.0


def test_one_existing_ticker_keeps_twenty_percent_cash() -> None:
    snapshot = equal_weight_existing_snapshot(("M1.L",), as_of=date(2026, 8, 30))
    assert snapshot.positions[0].ticker == "M1.L"
    assert snapshot.positions[0].current_weight_pct == 80.0
    assert snapshot.cash_weight_pct == 20.0
