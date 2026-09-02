"""Builders for sterling ledger test fixtures."""

from decimal import Decimal

from discount_analyst.domain.allocations.snapshot import SterlingPosition


def sterling_holdings(
    *tickers: str, value_gbp: Decimal = Decimal("1000.00")
) -> tuple[SterlingPosition, ...]:
    return tuple(
        SterlingPosition(ticker=ticker, value_gbp=value_gbp) for ticker in tickers
    )
