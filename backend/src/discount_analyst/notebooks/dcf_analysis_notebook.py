import marimo

__generated_with = "0.17.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    from discount_analyst.dcf_analysis.dcf_analysis import DCFAnalysis
    from discount_analyst.dcf_analysis.data_types import DCFAnalysisParameters

    return DCFAnalysis, DCFAnalysisParameters


@app.cell
def _(mo):
    mo.md(r"""
    # Constants
    """)
    return


@app.cell
def _():
    current_risk_free_rate = 0.04
    expected_market_return = 0.10
    assumed_us_tax_rate = 0.21
    return assumed_us_tax_rate, current_risk_free_rate, expected_market_return


@app.cell
def _(mo):
    mo.md(r"""
    # Marvell Technology, Inc.
    """)
    return


@app.cell
def _(
    DCFAnalysisParameters,
    assumed_us_tax_rate,
    current_risk_free_rate,
    expected_market_return,
):
    marvell_technology_dcf_analysis_params = DCFAnalysisParameters.model_validate(
        {
            "risk_free_rate": current_risk_free_rate,
            "expected_market_return": expected_market_return,
            "assumed_tax_rate": assumed_us_tax_rate,
            "initial_ebit": 102_200_000,
            "initial_revenue": 7_230_000_000,
            "initial_capital_expenditure": 314_700_000,
            "n_shares_outstanding": 862_100_000,
            "market_cap": 74_530_000_000,
            "gross_debt": 4_780_000_000,
            "gross_debt_last_year": 4_450_000_000,
            "net_debt": 3_115_500,
            "total_interest_expense": 200_000_000,
            "beta": 1.92,
            "assumed_forecast_period_annual_revenue_growth_rate": 0.2,
            "assumed_perpetuity_cash_flow_growth_rate": 0.03,
            "assumed_ebit_margin": 0.5,
            "assumed_depreciation_and_amortization_rate": 0.0528,
            "assumed_capex_rate": 0.0494,
            "assumed_change_in_working_capital_rate": 0.01,
            "forecast_period_years": 7,
        }
    )
    return (marvell_technology_dcf_analysis_params,)


@app.cell
def _(DCFAnalysis, marvell_technology_dcf_analysis_params):
    marvell_technology_dcf_analysis = DCFAnalysis(
        marvell_technology_dcf_analysis_params
    )

    marvell_technology_dcf_analysis.dcf_analysis()
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Docusign Inc.
    """)
    return


@app.cell
def _(
    DCFAnalysisParameters,
    assumed_us_tax_rate,
    current_risk_free_rate,
    expected_market_return,
):
    docusign_dcf_analysis_params = DCFAnalysisParameters.model_validate(
        {
            "risk_free_rate": current_risk_free_rate,
            "expected_market_return": expected_market_return,
            "assumed_tax_rate": assumed_us_tax_rate,
            "initial_ebit": 291_879_000,
            "initial_revenue": 3_095_362_000,
            "initial_capital_expenditure": 104_004_000,
            "n_shares_outstanding": 201_100_000,
            "market_cap": 13_630_000_000,
            "gross_debt": 126_940_000,
            "gross_debt_last_year": 143_053_000,
            "net_debt": 524_200_000,
            "total_interest_expense": 1_550_000,
            "beta": 0.98,
            "assumed_forecast_period_annual_revenue_growth_rate": 0.08,
            "assumed_perpetuity_cash_flow_growth_rate": 0.025,
            "assumed_ebit_margin": 0.26,
            "assumed_depreciation_and_amortization_rate": 0.035,
            "assumed_capex_rate": 0.012,
            "assumed_change_in_working_capital_rate": 0.01,
            "forecast_period_years": 5,
        }
    )
    return (docusign_dcf_analysis_params,)


@app.cell
def _(DCFAnalysis, docusign_dcf_analysis_params):
    docusign_dcf_analysis = DCFAnalysis(docusign_dcf_analysis_params)

    docusign_dcf_analysis.dcf_analysis()
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Amazon
    """)
    return


@app.cell
def _(
    DCFAnalysisParameters,
    assumed_us_tax_rate,
    current_risk_free_rate,
    expected_market_return,
):
    amazon_dcf_analysis_params = DCFAnalysisParameters.model_validate(
        {
            "risk_free_rate": current_risk_free_rate,
            "expected_market_return": expected_market_return,
            "assumed_tax_rate": assumed_us_tax_rate,
            "initial_ebit": 95_220_000_000,
            "initial_revenue": 691_330_000_000,
            "initial_capital_expenditure": 120_131_000_000,
            "n_shares_outstanding": 10_690_000_000,
            "market_cap": 2_510_000_000_000,
            "gross_debt": 160_440_000_000,
            "gross_debt_last_year": 130_900_000_000,
            "net_debt": 66_240_000_000,
            "total_interest_expense": 2_300_000_000,
            "beta": 1.37,
            "assumed_forecast_period_annual_revenue_growth_rate": 0.10,
            "assumed_perpetuity_cash_flow_growth_rate": 0.03,
            "assumed_ebit_margin": 0.115,
            "assumed_depreciation_and_amortization_rate": 0.085,
            "assumed_capex_rate": 0.13,
            "assumed_change_in_working_capital_rate": -0.025,
            "forecast_period_years": 5,
        }
    )
    return (amazon_dcf_analysis_params,)


@app.cell
def _(DCFAnalysis, amazon_dcf_analysis_params):
    amazon_dcf_analysis = DCFAnalysis(amazon_dcf_analysis_params)

    amazon_dcf_analysis.dcf_analysis()
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Duolingo
    """)
    return


@app.cell
def _(
    DCFAnalysisParameters,
    assumed_us_tax_rate,
    current_risk_free_rate,
    expected_market_return,
):
    duolingo_dcf_analysis_params = DCFAnalysisParameters.model_validate(
        {
            "risk_free_rate": current_risk_free_rate,
            "expected_market_return": expected_market_return,
            "assumed_tax_rate": assumed_us_tax_rate,
            "initial_ebit": 105_998_000,
            "initial_revenue": 964_271_000,
            "initial_capital_expenditure": 16_293_000,
            "n_shares_outstanding": 40_010_000,
            "market_cap": 8_560_000_000,
            "gross_debt": 97_320_000,
            "gross_debt_last_year": 54_656_000,
            "net_debt": 1_020_000_000,
            "total_interest_expense": 43_800_000,
            "beta": 0.83,
            "assumed_forecast_period_annual_revenue_growth_rate": 0.25,
            "assumed_perpetuity_cash_flow_growth_rate": 0.03,
            "assumed_ebit_margin": 0.15,
            "assumed_depreciation_and_amortization_rate": 0.015,
            "assumed_capex_rate": 0.030,
            "assumed_change_in_working_capital_rate": 0.02,
            "forecast_period_years": 5,
        }
    )
    return (duolingo_dcf_analysis_params,)


@app.cell
def _(DCFAnalysis, duolingo_dcf_analysis_params):
    duolingo_dcf_analysis = DCFAnalysis(duolingo_dcf_analysis_params)

    duolingo_dcf_analysis.dcf_analysis()
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Datadog Inc.
    """)
    return


@app.cell
def _(
    DCFAnalysisParameters,
    assumed_us_tax_rate,
    current_risk_free_rate,
    expected_market_return,
):
    datadog_dcf_analysis_params = DCFAnalysisParameters.model_validate(
        {
            "risk_free_rate": current_risk_free_rate,
            "expected_market_return": expected_market_return,
            "assumed_tax_rate": assumed_us_tax_rate,
            "initial_ebit": 136_595_000,
            "initial_revenue": 3_211_691_000,
            "initial_capital_expenditure": 123_626_000,
            "n_shares_outstanding": 325_440_000,
            "market_cap": 64_880_000_000,
            "gross_debt": 1_280_000_000,
            "gross_debt_last_year": 1_842_180_000,
            "net_debt": -2_900_000_000,
            "total_interest_expense": 7_000_000,
            "beta": 1.23,
            "assumed_forecast_period_annual_revenue_growth_rate": 0.18,
            "assumed_perpetuity_cash_flow_growth_rate": 0.03,
            "assumed_ebit_margin": 0.22,
            "assumed_depreciation_and_amortization_rate": 0.02,
            "assumed_capex_rate": 0.03,
            "assumed_change_in_working_capital_rate": 0.01,
            "forecast_period_years": 10,
        }
    )
    return (datadog_dcf_analysis_params,)


@app.cell
def _(DCFAnalysis, datadog_dcf_analysis_params):
    datadog_dcf_analysis = DCFAnalysis(datadog_dcf_analysis_params)

    datadog_dcf_analysis.dcf_analysis()
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Figma Inc.
    """)
    return


@app.cell
def _(
    DCFAnalysisParameters,
    assumed_us_tax_rate,
    current_risk_free_rate,
    expected_market_return,
):
    figma_dcf_analysis_params = DCFAnalysisParameters.model_validate(
        {
            "risk_free_rate": current_risk_free_rate,
            "expected_market_return": expected_market_return,
            "assumed_tax_rate": assumed_us_tax_rate,
            "initial_ebit": -1_043_286_000,
            "initial_revenue": 968_957_000,
            "initial_capital_expenditure": 14_618_000,
            "n_shares_outstanding": 415_910_000,
            "market_cap": 19_100_000_000,
            "gross_debt": 61_240_000,
            "gross_debt_last_year": 28_770_000,
            "net_debt": 1_520_000_000,
            "total_interest_expense": 0,
            "beta": 1.5,
            "assumed_forecast_period_annual_revenue_growth_rate": 0.35,
            "assumed_perpetuity_cash_flow_growth_rate": 0.03,
            "assumed_ebit_margin": 0.20,
            "assumed_depreciation_and_amortization_rate": 0.02,
            "assumed_capex_rate": 0.04,
            "assumed_change_in_working_capital_rate": -0.02,
            "forecast_period_years": 10,
        }
    )
    return (figma_dcf_analysis_params,)


@app.cell
def _(DCFAnalysis, figma_dcf_analysis_params):
    figma_dcf_analysis = DCFAnalysis(figma_dcf_analysis_params)

    figma_dcf_analysis.dcf_analysis()
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Nebius Group N.V.
    """)
    return


@app.cell
def _(
    DCFAnalysisParameters,
    assumed_us_tax_rate,
    current_risk_free_rate,
    expected_market_return,
):
    nebius_group_dcf_analysis_params = DCFAnalysisParameters.model_validate(
        {
            "risk_free_rate": current_risk_free_rate,
            "expected_market_return": expected_market_return,
            "assumed_tax_rate": assumed_us_tax_rate,
            "initial_ebit": 88_800_000,
            "initial_revenue": 363_300_000,
            "initial_capital_expenditure": 2_427_700_000,
            "n_shares_outstanding": 218_160_000,
            "market_cap": 21_040_000_000,
            "gross_debt": 4_570_000_000,
            "gross_debt_last_year": 49_700_000,
            "net_debt": 938_000_000,
            "total_interest_expense": 14_700_000,
            "beta": 2.2,  # 3.09 taken from past year. Past 5 year beta is 1.12. 2.2 is recommended by claude as base case
            "assumed_forecast_period_annual_revenue_growth_rate": 0.80,
            "assumed_perpetuity_cash_flow_growth_rate": 0.03,
            "assumed_ebit_margin": 0.25,
            "assumed_depreciation_and_amortization_rate": 0.18,
            "assumed_capex_rate": 0.35,
            "assumed_change_in_working_capital_rate": -0.02,
            "forecast_period_years": 10,
        }
    )
    return (nebius_group_dcf_analysis_params,)


@app.cell
def _(DCFAnalysis, nebius_group_dcf_analysis_params):
    nebius_group_dcf_analysis = DCFAnalysis(nebius_group_dcf_analysis_params)

    nebius_group_dcf_analysis.dcf_analysis()
    return


if __name__ == "__main__":
    app.run()
