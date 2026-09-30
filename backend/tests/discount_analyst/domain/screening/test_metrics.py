"""Tests for screening free-cash-flow, CAGR, and yield arithmetic."""

import math
from datetime import date

import pytest

from discount_analyst.domain.screening.metrics import (
    fcf_yield_pct,
    free_cash_flow,
    metrics_within_tolerance,
    revenue_cagr_pct,
)


def test_free_cash_flow_uses_absolute_capex() -> None:
    # EnQuest-shaped yfinance row: capex is reported as a negative outflow.
    assert free_cash_flow(100.0, -30.0) == 70.0
    assert free_cash_flow(100.0, 30.0) == 70.0


def test_revenue_cagr_is_independent_of_input_order() -> None:
    oldest_first = [
        (date(2021, 12, 31), 100.0),
        (date(2022, 12, 31), 110.0),
        (date(2023, 12, 31), 121.0),
        (date(2024, 12, 31), 133.1),
    ]
    newest_first = list(reversed(oldest_first))

    growth = revenue_cagr_pct(newest_first)

    assert math.isclose(growth, revenue_cagr_pct(oldest_first))
    assert math.isclose(growth, 10.0)


def test_revenue_cagr_rejects_fewer_than_four_positive_years() -> None:
    observations = [
        (date(2022, 12, 31), 100.0),
        (date(2023, 12, 31), 110.0),
        (date(2024, 12, 31), -5.0),
    ]
    with pytest.raises(ValueError, match="exactly four"):
        revenue_cagr_pct(observations)


def test_fcf_yield_converts_with_caller_fx_rate() -> None:
    same_currency = fcf_yield_pct(
        free_cash_flow_amount=10.0,
        free_cash_flow_currency="GBP",
        market_cap=200.0,
        market_cap_currency="gbp",
        fx_rate_to_market_cap_currency=None,
    )
    converted = fcf_yield_pct(
        free_cash_flow_amount=10.0,
        free_cash_flow_currency="USD",
        market_cap=200.0,
        market_cap_currency="GBP",
        fx_rate_to_market_cap_currency=0.8,
    )

    assert same_currency == 5.0
    assert converted == 4.0


def test_fcf_yield_requires_fx_when_currencies_differ() -> None:
    with pytest.raises(ValueError, match="fx_rate_to_market_cap_currency"):
        fcf_yield_pct(
            free_cash_flow_amount=10.0,
            free_cash_flow_currency="USD",
            market_cap=200.0,
            market_cap_currency="GBP",
            fx_rate_to_market_cap_currency=None,
        )


def test_reported_metric_may_stay_null() -> None:
    assert metrics_within_tolerance(None, 12.0)
    assert metrics_within_tolerance(12.05, 12.0)
    assert not metrics_within_tolerance(12.2, 12.0)
    assert not metrics_within_tolerance(12.0, None)
