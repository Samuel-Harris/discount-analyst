"""Deterministic screening arithmetic for Surveyor free-cash-flow and revenue CAGR."""

from __future__ import annotations

from datetime import date
from math import isfinite

SCREENING_METRIC_TOLERANCE_PP = 0.1


def free_cash_flow(operating_cash_flow: float, capital_expenditure: float) -> float:
    """Operating cash flow minus the magnitude of capital expenditure.

    yfinance reports capital expenditure as a negative outflow. Subtracting the
    raw figure would add capex back. Both signs therefore reduce free cash flow
    by the absolute spend.
    """
    _require_finite("operating_cash_flow", operating_cash_flow)
    _require_finite("capital_expenditure", capital_expenditure)
    return operating_cash_flow - abs(capital_expenditure)


def revenue_cagr_pct(observations: list[tuple[date, float]]) -> float:
    """Three-year revenue CAGR, in percentage points, from exactly four years.

    Observations are sorted by period end ascending before the ratio is taken,
    so a newest-first list cannot flip the sign. The span is the three steps
    between four annual observations: ``(newest / oldest) ** (1 / 3) - 1``.
    """
    if len(observations) != 4:
        msg = "revenue CAGR requires exactly four observations."
        raise ValueError(msg)
    ordered = sorted(observations, key=lambda item: item[0])
    period_ends = [period_end for period_end, _revenue in ordered]
    if len(set(period_ends)) != 4:
        msg = "revenue observations must have distinct period ends."
        raise ValueError(msg)
    revenues = [revenue for _period_end, revenue in ordered]
    for revenue in revenues:
        _require_finite("revenue", revenue)
        if revenue <= 0:
            msg = "revenue CAGR requires four strictly positive revenues."
            raise ValueError(msg)
    oldest = revenues[0]
    newest = revenues[-1]
    return ((newest / oldest) ** (1 / 3) - 1) * 100


def fcf_yield_pct(
    *,
    free_cash_flow_amount: float,
    free_cash_flow_currency: str,
    market_cap: float,
    market_cap_currency: str,
    fx_rate_to_market_cap_currency: float | None,
) -> float:
    """Free-cash-flow yield as a percentage of market cap.

    ``fx_rate_to_market_cap_currency`` is units of market-cap currency per one
    unit of free-cash-flow currency. It is required only when the currencies
    differ. This function does not fetch a rate.
    """
    _require_finite("free_cash_flow_amount", free_cash_flow_amount)
    _require_finite("market_cap", market_cap)
    if market_cap <= 0:
        msg = f"market_cap must be positive, got {market_cap}."
        raise ValueError(msg)
    flow_currency = free_cash_flow_currency.strip().upper()
    cap_currency = market_cap_currency.strip().upper()
    if not flow_currency or not cap_currency:
        msg = "free cash flow and market cap currencies are required."
        raise ValueError(msg)
    amount_in_cap_currency = free_cash_flow_amount
    if flow_currency != cap_currency:
        if fx_rate_to_market_cap_currency is None:
            msg = (
                "fx_rate_to_market_cap_currency is required when free cash flow "
                f"is {flow_currency} and market cap is {cap_currency}."
            )
            raise ValueError(msg)
        _require_finite(
            "fx_rate_to_market_cap_currency", fx_rate_to_market_cap_currency
        )
        if fx_rate_to_market_cap_currency <= 0:
            msg = "fx_rate_to_market_cap_currency must be positive."
            raise ValueError(msg)
        amount_in_cap_currency = free_cash_flow_amount * fx_rate_to_market_cap_currency
    return amount_in_cap_currency / market_cap * 100


def metrics_within_tolerance(reported: float | None, computed: float | None) -> bool:
    """True when a reported percentage matches the tool, or the report is null."""
    if reported is None:
        return True
    if computed is None:
        return False
    return abs(reported - computed) <= SCREENING_METRIC_TOLERANCE_PP


def _require_finite(name: str, value: float) -> None:
    if not isfinite(value):
        msg = f"{name} must be finite, got {value}."
        raise ValueError(msg)
