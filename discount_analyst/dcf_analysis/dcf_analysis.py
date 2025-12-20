from discount_analyst.dcf_analysis.data_types import (
    DCFAnalysisParameters,
    DCFAnalysisResult,
)


class DCFAnalysis:
    def __init__(
        self,
        dcf_analysis_params: DCFAnalysisParameters,
        /,
    ) -> None:
        stock_data = dcf_analysis_params.stock_data
        stock_assumptions = dcf_analysis_params.stock_assumptions

        # Initial financial state (from stock_data)
        self.initial_ebit = stock_data.ebit
        self.initial_revenue = stock_data.revenue
        self.initial_capital_expenditure = stock_data.capital_expenditure
        self.n_shares_outstanding = stock_data.n_shares_outstanding
        self.market_cap = stock_data.market_cap
        self.gross_debt = stock_data.gross_debt
        self.gross_debt_last_year = stock_data.gross_debt_last_year
        self.net_debt = stock_data.net_debt
        self.total_interest_expense = stock_data.total_interest_expense
        self.beta = stock_data.beta

        # Market parameters (from dcf_analysis_params directly)
        self.risk_free_rate = dcf_analysis_params.risk_free_rate
        self.expected_market_return = dcf_analysis_params.expected_market_return

        # Assumptions (from stock_assumptions)
        self.assumed_forecast_period_annual_revenue_growth_rate = (
            stock_assumptions.assumed_forecast_period_annual_revenue_growth_rate
        )
        self.assumed_perpetuity_cash_flow_growth_rate = (
            stock_assumptions.assumed_perpetuity_cash_flow_growth_rate
        )
        self.assumed_ebit_margin = stock_assumptions.assumed_ebit_margin
        self.assumed_tax_rate = stock_assumptions.assumed_tax_rate
        self.assumed_depreciation_and_amortization_rate = (
            stock_assumptions.assumed_depreciation_and_amortization_rate
        )
        self.assumed_capex_rate = stock_assumptions.assumed_capex_rate
        self.assumed_change_in_working_capital_rate = (
            stock_assumptions.assumed_change_in_working_capital_rate
        )

        # Input parameters (from stock_assumptions)
        self.forecast_period_years = stock_assumptions.forecast_period_years
        if self.forecast_period_years <= 0:
            raise ValueError(
                f"Forecast period years must be greater than 0. "
                f"Provided value: {self.forecast_period_years}. "
                f"Expected: positive integer (e.g., 5, 7, 10)."
            )

        if (
            self.assumed_forecast_period_annual_revenue_growth_rate
            <= self.assumed_perpetuity_cash_flow_growth_rate
        ):
            raise ValueError(
                f"Forecast period revenue growth rate ({self.assumed_forecast_period_annual_revenue_growth_rate:.4f}) "
                f"must be greater than perpetuity cash flow growth rate ({self.assumed_perpetuity_cash_flow_growth_rate:.4f}). "
                f"This ensures the company transitions from high-growth to stable growth. "
                f"Expected: forecast rate > perpetuity rate (e.g., 0.08 > 0.025)."
            )

    def _calculate_cost_of_equity(self) -> float:
        """Capital Asset Pricing Model (CAPM) approach"""

        equity_risk = self.expected_market_return - self.risk_free_rate

        return self.risk_free_rate + self.beta * equity_risk

    def _calculate_cost_of_debt(self) -> float:
        """Direct calculation from financial statement"""

        average_gross_debt = (self.gross_debt + self.gross_debt_last_year) / 2

        if average_gross_debt == 0:
            return 0.0

        return self.total_interest_expense / average_gross_debt

    def _calculate_discount_rate(self) -> float:
        """Weighted Average Cost of Capital (WACC)"""

        total_value = self.market_cap + self.gross_debt
        weight_of_equity = self.market_cap / total_value
        weight_of_debt = self.gross_debt / total_value

        cost_of_equity = self._calculate_cost_of_equity()
        cost_of_debt = self._calculate_cost_of_debt()
        after_tax_cost_of_debt = cost_of_debt * (1 - self.assumed_tax_rate)

        wacc = (
            weight_of_equity * cost_of_equity + weight_of_debt * after_tax_cost_of_debt
        )

        return wacc

    def _project_revenue_growth(self) -> list[float]:
        """Assuming a constant cumulative revenue growth rate"""

        projected_revenues = [
            self.initial_revenue
            * ((1 + self.assumed_forecast_period_annual_revenue_growth_rate) ** year)
            for year in range(1, self.forecast_period_years + 1)
        ]

        return projected_revenues

    def _forecast_free_cash_flows(self) -> list[float]:
        """Bottom-Up/Line-Item approach for FCF projection"""

        projected_revenues = self._project_revenue_growth()

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

    def _calculate_terminal_value(
        self,
        final_free_cash_flow: float,
        discount_rate: float,
    ) -> float:
        if discount_rate <= self.assumed_perpetuity_cash_flow_growth_rate:
            raise ValueError(
                f"Discount rate ({discount_rate:.4f}) must be strictly greater than "
                f"perpetuity growth rate ({self.assumed_perpetuity_cash_flow_growth_rate:.4f}) "
                f"for terminal value calculation. Provided discount rate: {discount_rate:.4f}. "
                f"Expected: discount rate > perpetuity rate (e.g., 0.08 > 0.025) to ensure convergence."
            )

        return (
            final_free_cash_flow
            * (1 + self.assumed_perpetuity_cash_flow_growth_rate)
            / (discount_rate - self.assumed_perpetuity_cash_flow_growth_rate)
        )

    def _calculate_present_values_of_forecasted_free_cash_flows(
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

    def _calculate_enterprise_value(self) -> float:
        discount_rate = self._calculate_discount_rate()

        forecasted_free_cash_flows = self._forecast_free_cash_flows()

        present_value_of_forecasted_free_cash_flows = (
            self._calculate_present_values_of_forecasted_free_cash_flows(
                forecasted_free_cash_flows=forecasted_free_cash_flows,
                discount_rate=discount_rate,
            )
        )

        if (
            len(present_value_of_forecasted_free_cash_flows)
            != self.forecast_period_years
        ):
            raise ValueError(
                f"Present value calculation mismatch. Expected {self.forecast_period_years} values "
                f"(one for each forecast year), but received {len(present_value_of_forecasted_free_cash_flows)} values. "
                f"This indicates an internal calculation error in the DCF model."
            )

        terminal_value = self._calculate_terminal_value(
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
        enterprise_value = self._calculate_enterprise_value()

        equity_value = enterprise_value - self.net_debt
        intrinsic_share_price = equity_value / self.n_shares_outstanding

        return DCFAnalysisResult(
            intrinsic_share_price=intrinsic_share_price,
            enterprise_value=enterprise_value,
            equity_value=equity_value,
        )
