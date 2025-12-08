from pydantic import BaseModel, Field, computed_field


class StockData(BaseModel):
    ticker: str = Field(
        description="The stock ticker symbol (e.g., 'AAPL', 'MSFT', 'TSLA'). Used to uniquely identify the company in financial markets."
    )
    name: str = Field(
        description="The full legal or common name of the company (e.g., 'Apple Inc.', 'Microsoft Corporation'). This is the official company name as reported in regulatory filings."
    )

    # Income Statement Metrics
    ebit: float = Field(
        description="Earnings Before Interest and Taxes (EBIT) in currency units (USD). Also known as Operating Income. This is the company's profit from operations before financing costs and taxes. Formula: Revenue - Cost of Goods Sold - Operating Expenses. Used to calculate operating cash flows in DCF analysis."
    )
    revenue: float = Field(
        description="Total revenue (top-line sales) in currency units (USD). This is the company's total sales from all business operations for the most recent fiscal period. Also called 'net sales' or 'turnover'. Used as the baseline for calculating margin ratios and projecting future growth."
    )

    # Cash Flow Statement Metrics
    capital_expenditure: float = Field(
        description="Capital Expenditures (CapEx) in currency units (USD). Cash spent on acquiring or maintaining physical assets like property, plants, and equipment. Found in the Cash Flow from Investing Activities section. Used to calculate Free Cash Flow (FCF = Operating Cash Flow - CapEx). Positive value represents cash outflow."
    )

    # Market Data
    n_shares_outstanding: float = Field(
        description="Number of shares outstanding (fully diluted). Total number of shares currently held by all shareholders, including restricted shares and those held by insiders. Used to calculate per-share metrics and to convert equity value to per-share price."
    )
    market_cap: float = Field(
        description="Market Capitalization (Equity Value) in currency units (USD). Current market value of all outstanding shares. Formula: Share Price × Shares Outstanding. Represents what the market believes the company's equity is worth. Used as a sanity check against DCF-derived equity value."
    )

    # Balance Sheet - Debt Metrics
    gross_debt: float = Field(
        description="Total Gross Debt (current period) in currency units (USD). Sum of all short-term and long-term debt obligations, including bonds, loans, and credit facilities. Found on the liabilities side of the balance sheet. Does NOT subtract cash. Used to calculate Enterprise Value (EV = Market Cap + Net Debt)."
    )
    gross_debt_last_year: float = Field(
        description="Total Gross Debt from the prior fiscal year in currency units (USD). Used to calculate year-over-year change in debt levels and to assess debt repayment or issuance trends. Helps validate interest expense calculations."
    )
    net_debt: float = Field(
        description="Net Debt in currency units (USD). Formula: Gross Debt - Cash and Cash Equivalents. Can be negative if the company has more cash than debt (net cash position). Used in Enterprise Value calculation: EV = Market Cap + Net Debt. Represents the debt that would remain if all cash were used to pay down obligations."
    )

    # Income Statement - Financing Costs
    total_interest_expense: float = Field(
        description="Total Interest Expense in currency units (USD). Cash paid or accrued for interest on debt obligations during the period. Found in the Income Statement, typically below EBIT. Used to calculate the effective interest rate on debt: Interest Rate = Interest Expense / Average Debt. Important for WACC calculation and understanding the cost of debt financing."
    )

    # Risk Metric
    beta: float = Field(
        description="Beta coefficient (dimensionless). Measures the stock's volatility relative to the overall market (typically S&P 500). Beta = 1.0 means the stock moves in line with the market. Beta > 1.0 means the stock is more volatile than the market (higher risk). Beta < 1.0 means the stock is less volatile than the market (lower risk). Used in CAPM to calculate Cost of Equity: Re = Rf + Beta × (Rm - Rf). Typically measured over 2-5 years of historical data."
    )

    @computed_field
    @property
    def enterprise_value(self) -> float:
        """
        Calculated Enterprise Value (EV) in currency units.
        Formula: Market Cap + Net Debt
        Represents the total value of the company's operations.
        """

        return self.market_cap + self.net_debt

    @computed_field
    @property
    def ebit_margin(self) -> float:
        """
        Calculated EBIT Margin as a decimal (e.g., 0.15 for 15%).
        Formula: EBIT / Revenue
        Measures operating profitability.
        """

        if self.revenue == 0:
            return 0.0
        return self.ebit / self.revenue

    @computed_field
    @property
    def implied_interest_rate(self) -> float:
        """
        Calculated implied interest rate on debt as a decimal (e.g., 0.045 for 4.5%).
        Formula: Total Interest Expense / Average Gross Debt
        Represents the company's effective cost of debt.
        """
        avg_debt = (self.gross_debt + self.gross_debt_last_year) / 2
        if avg_debt == 0:
            return 0.0
        return self.total_interest_expense / avg_debt

    @computed_field
    @property
    def capex_as_percentage_of_revenue(self) -> float:
        """
        Calculated CapEx as a percentage of revenue, expressed as a decimal (e.g., 0.06 for 6%).
        Formula: Capital Expenditure / Revenue
        Measures capital intensity and investment requirements relative to sales.
        Used as a baseline for the 'assumed_capex_rate' in DCF projections.
        Higher values indicate capital-intensive businesses (manufacturing, infrastructure).
        Lower values indicate asset-light businesses (software, services).
        """

        if self.revenue == 0:
            return 0.0
        return self.capital_expenditure / self.revenue

    @computed_field
    @property
    def debt_trend(self) -> float:
        """
        Calculated debt trend as a percentage (e.g., -0.075 for -7.5%).
        Formula: (Gross Debt - Gross Debt Last Year) / Gross Debt Last Year
        Represents the change in debt levels over the period. Positive = adding debt, Negative = paying down debt.
        """

        if self.gross_debt_last_year == 0:
            return 0.0
        return (self.gross_debt - self.gross_debt_last_year) / self.gross_debt_last_year

    @computed_field
    @property
    def company_scale(self) -> str:
        """
        Calculated company scale based on revenue.
        Large cap (typically mature), Mid-large cap (growth or mature), Mid cap (often growth stage), Small cap (high growth potential), or Micro cap (very high growth potential).
        """
        if self.revenue > 50_000_000_000:
            return "Large Cap"
        elif self.revenue > 10_000_000_000:
            return "Mid Cap"
        elif self.revenue > 1_000_000_000:
            return "Small Cap"
        else:
            return "Micro Cap"


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
