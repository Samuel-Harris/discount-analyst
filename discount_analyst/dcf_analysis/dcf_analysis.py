from discount_analyst.dcf_analysis.types import DCFAnalysisParameters, DCFAnalysisResult


class DCFAnalysis:
    def __init__(
        self,
        dcf_analysis_params: DCFAnalysisParameters,
    ) -> None:
        # Initial financial state
        self.initial_ebit = dcf_analysis_params.initial_ebit
        self.initial_revenue = dcf_analysis_params.initial_revenue
        self.initial_capital_expenditure = (
            dcf_analysis_params.initial_capital_expenditure
        )
        self.n_shares_outstanding = dcf_analysis_params.n_shares_outstanding
        self.equity_value = dcf_analysis_params.equity_value
        self.gross_debt = dcf_analysis_params.gross_debt
        self.gross_debt_last_year = dcf_analysis_params.gross_debt_last_year
        self.net_debt = dcf_analysis_params.net_debt
        self.total_interest_expense = dcf_analysis_params.total_interest_expense
        self.risk_free_rate = dcf_analysis_params.risk_free_rate
        self.beta = dcf_analysis_params.beta

        # Assumptions
        self.assumed_forecast_period_annual_revenue_growth_rate = (
            dcf_analysis_params.assumed_forecast_period_annual_revenue_growth_rate
        )
        self.assumed_perpetuity_cash_flow_growth_rate = (
            dcf_analysis_params.assumed_perpetuity_cash_flow_growth_rate
        )
        self.assumed_ebit_margin = dcf_analysis_params.assumed_ebit_margin
        self.assumed_tax_rate = dcf_analysis_params.assumed_tax_rate
        self.assumed_depreciation_and_amortization_rate = (
            dcf_analysis_params.assumed_depreciation_rate
        )
        self.assumed_capex_rate = dcf_analysis_params.assumed_capex_rate
        self.assumed_change_in_working_capital_rate = (
            dcf_analysis_params.assumed_change_in_working_capital_rate
        )
        self.expected_market_return = dcf_analysis_params.expected_market_return

        # Input parameters
        self.forecast_period_years = dcf_analysis_params.forecast_period_years

    def calculate_cost_of_equity(self) -> float:
        """Capital Asset Pricing Model (CAPM) approach"""

        equity_risk = self.expected_market_return - self.risk_free_rate

        return self.risk_free_rate + self.beta * equity_risk

    def calculate_cost_of_debt(self) -> float:
        """Direct calculation from financial statement"""

        average_gross_debt = (self.gross_debt + self.gross_debt_last_year) / 2

        return self.total_interest_expense / average_gross_debt

    def calculate_discount_rate(self) -> float:
        """Weighted Average Cost of Capital (WACC)"""

        total_value = self.equity_value + self.gross_debt
        weight_of_equity = self.equity_value / total_value
        weight_of_debt = self.gross_debt / total_value

        cost_of_equity = self.calculate_cost_of_equity()
        cost_of_debt = self.calculate_cost_of_debt()
        after_tax_cost_of_debt = cost_of_debt * (1 - self.assumed_tax_rate)

        wacc = (
            weight_of_equity * cost_of_equity + weight_of_debt * after_tax_cost_of_debt
        )

        return wacc

    def project_revenue_growth(self) -> list[float]:
        """Assuming a constant cumulative revenue growth rate"""

        projected_revenues = [
            self.initial_revenue
            * ((1 + self.assumed_forecast_period_annual_revenue_growth_rate) ** year)
            for year in range(1, self.forecast_period_years + 1)
        ]

        return projected_revenues

    def forecast_free_cash_flows(self) -> list[float]:
        """Bottom-Up/Line-Item approach for FCF projection"""

        projected_revenues = self.project_revenue_growth()

        forecasted_free_cash_flows: list[float] = []
        previous_revenue = self.initial_revenue

        for projected_revenue in projected_revenues:
            ebit = projected_revenue * self.assumed_ebit_margin
            nopat = ebit * (1 - self.assumed_tax_rate)

            depreciation_and_amortization = (
                projected_revenue * self.assumed_depreciation_and_amortization_rate
            )
            capex = projected_revenue * self.assumed_capex_rate

            revenue_growth = projected_revenue - previous_revenue
            change_in_working_capital = (
                revenue_growth * self.assumed_change_in_working_capital_rate
            )

            forecasted_free_cash_flow = (
                nopat
                + depreciation_and_amortization
                - capex
                - change_in_working_capital
            )
            forecasted_free_cash_flows.append(forecasted_free_cash_flow)

            previous_revenue = projected_revenue

        return forecasted_free_cash_flows

    def calculate_terminal_value(
        self,
        final_free_cash_flow: float,
        discount_rate: float,
    ) -> float:
        return (
            final_free_cash_flow
            * (1 + self.assumed_perpetuity_cash_flow_growth_rate)
            / (discount_rate - self.assumed_perpetuity_cash_flow_growth_rate)
        )

    def calculate_present_values_of_forecasted_free_cash_flows(
        self,
        forecasted_free_cash_flows: list[float],
        discount_rate: float,
    ) -> list[float]:
        return [
            forecast_free_cash_flow / (1 + discount_rate) ** year
            for year, forecast_free_cash_flow in enumerate(
                forecasted_free_cash_flows, start=1
            )
        ]

    def calculate_enterprise_value(self) -> float:
        discount_rate = self.calculate_discount_rate()

        forecasted_free_cash_flows = self.forecast_free_cash_flows()

        present_value_of_forecasted_free_cash_flows = (
            self.calculate_present_values_of_forecasted_free_cash_flows(
                forecasted_free_cash_flows=forecasted_free_cash_flows,
                discount_rate=discount_rate,
            )
        )

        if (
            len(present_value_of_forecasted_free_cash_flows)
            != self.forecast_period_years
        ):
            raise ValueError(
                f"Expected to generate the present values for the next {self.forecast_period_years} years. Only generated {len(present_value_of_forecasted_free_cash_flows)} present values."
            )

        terminal_value = self.calculate_terminal_value(
            final_free_cash_flow=forecasted_free_cash_flows[-1],
            discount_rate=discount_rate,
        )
        present_value_of_terminal_value = (
            terminal_value / (1 + discount_rate) ** self.forecast_period_years
        )

        return present_value_of_terminal_value + sum(
            present_value_of_forecasted_free_cash_flows
        )

    def dcf_analysis(self) -> DCFAnalysisResult:
        enterprise_value = self.calculate_enterprise_value()

        equity_value = enterprise_value - self.net_debt
        intrinsic_share_price = equity_value / self.n_shares_outstanding

        return DCFAnalysisResult(
            intrinsic_share_price=intrinsic_share_price,
        )
