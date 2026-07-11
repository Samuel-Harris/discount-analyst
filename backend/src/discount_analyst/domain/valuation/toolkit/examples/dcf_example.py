"""Example terminal script using the optional DCF toolkit helpers."""

from discount_analyst.domain.valuation.toolkit.dcf import dcf_value_per_share


if __name__ == "__main__":
    result = dcf_value_per_share(
        revenue=100_000_000,
        revenue_growth_pct=6.0,
        ebit_margin_pct=15.0,
        tax_rate_pct=25.0,
        depreciation_amortisation_pct=3.0,
        capex_pct=4.0,
        change_working_capital_pct=1.0,
        years=5,
        discount_rate_pct=9.0,
        terminal_growth_pct=2.5,
        net_debt=10_000_000,
        shares_outstanding=50_000_000,
    )
    print(result["value_per_share"])
