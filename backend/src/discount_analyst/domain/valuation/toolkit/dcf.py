"""Small deterministic DCF primitives for Appraiser terminal analysis."""

from __future__ import annotations

from typing import cast


def _rate(pct: float) -> float:
    if pct <= -100:
        msg = f"Percentage rate must be greater than -100, got {pct}."
        raise ValueError(msg)
    return pct / 100


def discount_factor(*, discount_rate_pct: float, year: int) -> float:
    """Return the present-value discount factor for a 1-indexed forecast year."""
    if year <= 0:
        msg = f"year must be positive, got {year}."
        raise ValueError(msg)
    return 1 / ((1 + _rate(discount_rate_pct)) ** year)


def present_value(*, amount: float, discount_rate_pct: float, year: int) -> float:
    return amount * discount_factor(discount_rate_pct=discount_rate_pct, year=year)


def terminal_value_gordon(
    *,
    final_cash_flow: float,
    discount_rate_pct: float,
    terminal_growth_pct: float,
) -> float:
    """Gordon-growth terminal value, using percentage-point inputs."""
    discount_rate = _rate(discount_rate_pct)
    terminal_growth = _rate(terminal_growth_pct)
    if discount_rate <= terminal_growth:
        msg = (
            "discount_rate_pct must be greater than terminal_growth_pct for "
            "Gordon-growth terminal value."
        )
        raise ValueError(msg)
    return final_cash_flow * (1 + terminal_growth) / (discount_rate - terminal_growth)


def project_compound_series(
    *, starting_value: float, annual_growth_pct: float, years: int
) -> list[float]:
    if years <= 0:
        msg = f"years must be positive, got {years}."
        raise ValueError(msg)
    growth = _rate(annual_growth_pct)
    return [starting_value * ((1 + growth) ** year) for year in range(1, years + 1)]


def fcff_projection(
    *,
    revenue: float,
    revenue_growth_pct: float,
    ebit_margin_pct: float,
    tax_rate_pct: float,
    depreciation_amortisation_pct: float,
    capex_pct: float,
    change_working_capital_pct: float,
    years: int,
) -> list[dict[str, float]]:
    """Project FCFF using simple revenue and percentage-of-revenue assumptions."""
    projected_revenue = project_compound_series(
        starting_value=revenue,
        annual_growth_pct=revenue_growth_pct,
        years=years,
    )
    ebit_margin = _rate(ebit_margin_pct)
    tax_rate = _rate(tax_rate_pct)
    da_rate = _rate(depreciation_amortisation_pct)
    capex_rate = _rate(capex_pct)
    wc_rate = _rate(change_working_capital_pct)
    previous_revenue = revenue
    rows: list[dict[str, float]] = []
    for year, next_revenue in enumerate(projected_revenue, start=1):
        ebit = next_revenue * ebit_margin
        nopat = ebit * (1 - tax_rate)
        depreciation_amortisation = next_revenue * da_rate
        capex = next_revenue * capex_rate
        change_working_capital = (next_revenue - previous_revenue) * wc_rate
        fcff = nopat + depreciation_amortisation - capex - change_working_capital
        rows.append(
            {
                "year": float(year),
                "revenue": next_revenue,
                "ebit": ebit,
                "nopat": nopat,
                "depreciation_amortisation": depreciation_amortisation,
                "capex": capex,
                "change_working_capital": change_working_capital,
                "fcff": fcff,
            }
        )
        previous_revenue = next_revenue
    return rows


def dcf_equity_value(
    *,
    fcff: list[float],
    discount_rate_pct: float,
    terminal_growth_pct: float,
    net_debt: float,
) -> dict[str, float | list[float]]:
    if not fcff:
        raise ValueError("fcff must contain at least one forecast cash flow.")
    pv_fcff = [
        present_value(amount=value, discount_rate_pct=discount_rate_pct, year=year)
        for year, value in enumerate(fcff, start=1)
    ]
    terminal_value = terminal_value_gordon(
        final_cash_flow=fcff[-1],
        discount_rate_pct=discount_rate_pct,
        terminal_growth_pct=terminal_growth_pct,
    )
    pv_terminal_value = present_value(
        amount=terminal_value,
        discount_rate_pct=discount_rate_pct,
        year=len(fcff),
    )
    enterprise_value = sum(pv_fcff) + pv_terminal_value
    equity_value = enterprise_value - net_debt
    return {
        "pv_fcff": pv_fcff,
        "terminal_value": terminal_value,
        "pv_terminal_value": pv_terminal_value,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
    }


def dcf_value_per_share(
    *,
    revenue: float,
    revenue_growth_pct: float,
    ebit_margin_pct: float,
    tax_rate_pct: float,
    depreciation_amortisation_pct: float,
    capex_pct: float,
    change_working_capital_pct: float,
    years: int,
    discount_rate_pct: float,
    terminal_growth_pct: float,
    net_debt: float,
    shares_outstanding: float,
) -> dict[str, object]:
    if shares_outstanding <= 0:
        msg = f"shares_outstanding must be positive, got {shares_outstanding}."
        raise ValueError(msg)
    rows = fcff_projection(
        revenue=revenue,
        revenue_growth_pct=revenue_growth_pct,
        ebit_margin_pct=ebit_margin_pct,
        tax_rate_pct=tax_rate_pct,
        depreciation_amortisation_pct=depreciation_amortisation_pct,
        capex_pct=capex_pct,
        change_working_capital_pct=change_working_capital_pct,
        years=years,
    )
    valuation = dcf_equity_value(
        fcff=[row["fcff"] for row in rows],
        discount_rate_pct=discount_rate_pct,
        terminal_growth_pct=terminal_growth_pct,
        net_debt=net_debt,
    )
    equity_value = cast(float, valuation["equity_value"])
    return {
        "value_per_share": equity_value / shares_outstanding,
        "projection": rows,
        **valuation,
    }
