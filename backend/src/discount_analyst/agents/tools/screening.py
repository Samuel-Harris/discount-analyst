"""Host-side Surveyor screening arithmetic. The sandbox cannot import this package."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field
from pydantic_ai import FunctionToolset

from discount_analyst.agents.tools.terminal.infallible_toolset import InfallibleToolset
from discount_analyst.domain.screening.metrics import (
    fcf_yield_pct,
    free_cash_flow,
    revenue_cagr_pct,
)

COMPUTE_SCREENING_METRICS_TOOL = "compute_screening_metrics"


class RevenueObservation(BaseModel):
    """One annual revenue observation for the three-year CAGR."""

    period_end: date = Field(description="Fiscal period end for this revenue figure.")
    revenue: float = Field(description="Revenue for the period, in statement currency.")


class ScreeningMetricsResult(BaseModel):
    """Figures the Surveyor must copy. Null means the inputs were not usable."""

    ticker: str
    free_cash_flow: float | None
    free_cash_flow_yield_pct: float | None
    revenue_growth_3y_cagr_pct: float | None


def compute_screening_metrics(
    ticker: str,
    operating_cash_flow: float | None = None,
    capital_expenditure: float | None = None,
    free_cash_flow_currency: str | None = None,
    market_cap: float | None = None,
    market_cap_currency: str | None = None,
    fx_rate_to_market_cap_currency: float | None = None,
    revenue_observations: list[RevenueObservation] | None = None,
) -> ScreeningMetricsResult:
    """Compute free-cash-flow yield and three-year revenue CAGR for one ticker.

    Pass statement rows; do not pre-compute the percentages. Capital expenditure
    may be negative (yfinance) or positive. ``fx_rate_to_market_cap_currency``
    is units of market-cap currency per one unit of free-cash-flow currency,
    and is required only when those currencies differ. Omit
    ``revenue_observations``, or pass fewer than four comparable years, to
    receive a null CAGR. A null field must be copied as null.

    Args:
        ticker: Listing symbol the result belongs to, for example ``ENQ.L``.
        operating_cash_flow: Latest annual operating cash flow, or null.
        capital_expenditure: Latest annual capital expenditure, signed or not.
        free_cash_flow_currency: ISO currency of the cash-flow figures.
        market_cap: Market cap in ``market_cap_currency``. Must be positive
            when a yield is requested.
        market_cap_currency: ISO currency of ``market_cap`` (GBP or USD).
        fx_rate_to_market_cap_currency: Caller-supplied FX rate into the
            market-cap currency. Not fetched here.
        revenue_observations: Exactly four strictly positive annual revenues
            when a three-year CAGR is required.

    Returns:
        The cash-flow amount and the two percentages, with nulls where the
        inputs could not support a figure.
    """
    flow = _free_cash_flow_or_null(operating_cash_flow, capital_expenditure)
    yield_pct = _yield_or_null(
        free_cash_flow_amount=flow,
        free_cash_flow_currency=free_cash_flow_currency,
        market_cap=market_cap,
        market_cap_currency=market_cap_currency,
        fx_rate_to_market_cap_currency=fx_rate_to_market_cap_currency,
    )
    growth = _cagr_or_null(revenue_observations)
    return ScreeningMetricsResult(
        ticker=ticker,
        free_cash_flow=flow,
        free_cash_flow_yield_pct=yield_pct,
        revenue_growth_3y_cagr_pct=growth,
    )


def _free_cash_flow_or_null(
    operating_cash_flow: float | None,
    capital_expenditure: float | None,
) -> float | None:
    if operating_cash_flow is None or capital_expenditure is None:
        return None
    try:
        return free_cash_flow(operating_cash_flow, capital_expenditure)
    except ValueError:
        return None


def _yield_or_null(
    *,
    free_cash_flow_amount: float | None,
    free_cash_flow_currency: str | None,
    market_cap: float | None,
    market_cap_currency: str | None,
    fx_rate_to_market_cap_currency: float | None,
) -> float | None:
    if (
        free_cash_flow_amount is None
        or free_cash_flow_currency is None
        or market_cap is None
        or market_cap_currency is None
    ):
        return None
    try:
        return fcf_yield_pct(
            free_cash_flow_amount=free_cash_flow_amount,
            free_cash_flow_currency=free_cash_flow_currency,
            market_cap=market_cap,
            market_cap_currency=market_cap_currency,
            fx_rate_to_market_cap_currency=fx_rate_to_market_cap_currency,
        )
    except ValueError:
        return None


def _cagr_or_null(
    revenue_observations: list[RevenueObservation] | None,
) -> float | None:
    if not revenue_observations:
        return None
    try:
        return revenue_cagr_pct(
            [
                (observation.period_end, observation.revenue)
                for observation in revenue_observations
            ]
        )
    except ValueError:
        return None


def create_screening_metrics_toolset() -> InfallibleToolset[None]:
    """Surveyor-only host tool for free-cash-flow yield and revenue CAGR."""
    toolset = FunctionToolset[None]()
    toolset.add_function(
        compute_screening_metrics,
        name=COMPUTE_SCREENING_METRICS_TOOL,
        docstring_format="google",
        require_parameter_descriptions=True,
    )
    return InfallibleToolset(toolset)
