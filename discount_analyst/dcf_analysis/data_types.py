from pydantic import BaseModel


class DCFAnalysisParameters(BaseModel):
    # Initial financial state
    initial_ebit: float
    initial_revenue: float
    initial_capital_expenditure: float
    n_shares_outstanding: float
    market_cap: float
    gross_debt: float
    gross_debt_last_year: float
    net_debt: float
    total_interest_expense: float
    risk_free_rate: float
    beta: float

    # Assumptions
    assumed_forecast_period_annual_revenue_growth_rate: float
    assumed_perpetuity_cash_flow_growth_rate: float
    assumed_ebit_margin: float
    assumed_tax_rate: float
    assumed_depreciation_and_amortization_rate: float  # As a percentage of revenue
    assumed_capex_rate: float  # As a percentage of revenue
    assumed_change_in_working_capital_rate: float  # As a percentage of revenue
    expected_market_return: float

    # Input parameters
    forecast_period_years: int


class DCFAnalysisResult(BaseModel):
    intrinsic_share_price: float
