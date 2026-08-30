"""Build a 100% snapshot that equal-weights existing tickers and leaves the rest in cash."""

from datetime import date

from discount_analyst.domain.allocations.snapshot import (
    CurrentPortfolioSnapshot,
    CurrentPositionWeight,
)

_DEFAULT_CASH_WEIGHT_PCT = 20.0


def equal_weight_existing_snapshot(
    tickers: tuple[str, ...],
    *,
    as_of: date,
    cash_weight_pct: float = _DEFAULT_CASH_WEIGHT_PCT,
) -> CurrentPortfolioSnapshot:
    """Return a snapshot whose positions plus cash total 100%.

    Used by mock dashboard runs. Live dashboard runners must load a real
    snapshot instead of calling this helper.
    """
    if not tickers:
        return CurrentPortfolioSnapshot(
            as_of=as_of,
            positions=(),
            cash_weight_pct=100.0,
        )
    equity_total = round(100.0 - cash_weight_pct, 2)
    weights = _split_total(equity_total, len(tickers))
    positions = tuple(
        CurrentPositionWeight(ticker=ticker, current_weight_pct=weight)
        for ticker, weight in zip(tickers, weights, strict=True)
    )
    cash = round(100.0 - sum(weight for weight in weights), 2)
    return CurrentPortfolioSnapshot(
        as_of=as_of,
        positions=positions,
        cash_weight_pct=cash,
    )


def _split_total(total: float, count: int) -> tuple[float, ...]:
    if count == 1:
        return (round(total, 2),)
    each = round(total / count, 2)
    head = tuple(each for _ in range(count - 1))
    tail = round(total - sum(head), 2)
    return (*head, tail)
