from pydantic import BaseModel, Field


class StockData(BaseModel):
    ticker: str
    name: str

    ebit: float
    revenue: float
    capital_expenditure: float
    n_shares_outstanding: float
    market_cap: float
    gross_debt: float
    gross_debt_last_year: float
    net_debt: float
    total_interest_expense: float
    beta: float


class StockAssumptions(BaseModel):
    forecast_period_years: int = Field(
        description="The number of years for the explicit forecast period before terminal value calculation. Typically 5 years for mature companies, 7-8 years for growing/transitioning companies, and 10 years for high-growth companies far from steady state."
    )
    assumed_tax_rate: float = Field(
        description="The assumed corporate tax rate as a decimal (e.g., 0.21 for 21%). Should reflect the lower of statutory rate or company's historical effective tax rate."
    )
    assumed_forecast_period_annual_revenue_growth_rate: float = Field(
        description="The assumed average annual revenue growth rate during the forecast period as a decimal (e.g., 0.15 for 15%). For companies with declining growth, this represents the geometric average across all forecast years. Must be greater than perpetuity growth rate."
    )
    assumed_perpetuity_cash_flow_growth_rate: float = Field(
        description="The assumed long-term sustainable growth rate of cash flows in perpetuity as a decimal (e.g., 0.025 for 2.5%). Should not exceed nominal GDP growth; typically 2.0-3.0%. Must be less than forecast period growth rate."
    )
    assumed_ebit_margin: float = Field(
        description="The assumed normalized/terminal EBIT margin as a decimal (e.g., 0.18 for 18%). Represents the expected steady-state operating margin at the end of the forecast period, typically benchmarked against peer group medians."
    )
    assumed_depreciation_and_amortization_rate: float = Field(
        description="The assumed depreciation and amortization rate as a percentage of revenue, expressed as a decimal (e.g., 0.05 for 5%). Based on historical median D&A/Revenue ratio."
    )
    assumed_capex_rate: float = Field(
        description="The assumed capital expenditure rate as a percentage of revenue, expressed as a decimal (e.g., 0.06 for 6%). Should reflect maintenance capex plus growth capex needs. For growth companies, typically exceeds D&A rate; for mature companies, approximately equals D&A rate."
    )
    assumed_change_in_working_capital_rate: float = Field(
        description="The assumed change in working capital as a percentage of revenue change, expressed as a decimal (e.g., 0.02 for 2%). Represents cash consumed by working capital as the business grows. Can be negative for companies with negative working capital models."
    )
