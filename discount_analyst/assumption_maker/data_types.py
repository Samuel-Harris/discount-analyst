from pydantic import BaseModel, Field


class StockAssumptions(BaseModel):
    assumed_tax_rate: float = Field(description="The assumed corporate tax rate.")
    assumed_forecast_period_annual_revenue_growth_rate: float = Field(
        description="The assumed annual revenue growth rate during the forecast period."
    )
    assumed_perpetuity_cash_flow_growth_rate: float = Field(
        description="The assumed growth rate of cash flows in perpetuity."
    )
    assumed_ebit_margin: float = Field(description="The assumed EBIT margin.")
    assumed_depreciation_and_amortization_rate: float = Field(
        description="The assumed depreciation and amortization rate as a percentage of revenue."
    )
    assumed_capex_rate: float = Field(
        description="The assumed capital expenditure rate as a percentage of revenue."
    )
    assumed_change_in_working_capital_rate: float = Field(
        description="The assumed change in working capital rate as a percentage of revenue."
    )
