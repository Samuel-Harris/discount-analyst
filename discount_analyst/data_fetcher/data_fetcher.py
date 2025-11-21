from typing import Any, cast
import yfinance as yf  # pyright: ignore[reportMissingTypeStubs]
import pandas as pd
from datetime import timedelta

from discount_analyst.data_fetcher.constants import (
    PREVIOUS_YEAR_DAYS_AGO_MIN_THRESHOLD,
    STATEMENT_DATE_WINDOW_DAYS,
)
from discount_analyst.data_fetcher.data_types import Statement, StockData
from logging import getLogger

logger = getLogger(__name__)


class DataFetcher:
    def _get_ordered_statements_from_df(
        self, statements: pd.DataFrame
    ) -> list[Statement] | None:
        """Get statements in ascending order of date"""

        statement_columns: Any | list = statements.columns.tolist()  # pyright: ignore[reportMissingTypeArgument, reportUnknownVariableType]
        if not isinstance(statement_columns, list):
            raise TypeError(
                f"Expected latest_annual_statement_date_strs to be a list. Got {type(statement_columns)}"
            )

        if not all(
            isinstance(date_str, pd.Timestamp)
            for date_str in statement_columns  # pyright: ignore[reportUnknownVariableType]
        ):
            raise TypeError(
                f"Not all annual statement column names were Pandas timestamps. Column names: {[statement_columns]}"
            )

        statement_pd_timestamps = cast(list[pd.Timestamp], statement_columns)

        if len(statement_pd_timestamps) == 0:
            return None

        return [
            Statement(
                date=statement_pd_timestamp.date(),
                statement=statements[statement_pd_timestamp],
            )
            for statement_pd_timestamp in sorted(statement_pd_timestamps)
        ]

    def _get_last_years_statement(
        self,
        latest_statement_pd_timestamp: pd.Timestamp,
        annual_statements: pd.DataFrame,
        quarterly_statements: pd.DataFrame,
        statement_name: str,
    ) -> pd.Series:
        ordered_annual_statements = self._get_ordered_statements_from_df(
            annual_statements
        )
        ordered_quarterly_statements = self._get_ordered_statements_from_df(
            quarterly_statements
        )

        latest_statement_date = latest_statement_pd_timestamp.date()
        mininmum_time_ago = timedelta(days=PREVIOUS_YEAR_DAYS_AGO_MIN_THRESHOLD)

        latest_annual_statement_over_a_year_ago = None
        if ordered_annual_statements:
            annual_statements_over_a_year_ago = [
                annual_statement
                for annual_statement in ordered_annual_statements
                if annual_statement.date <= latest_statement_date - mininmum_time_ago
            ]
            if annual_statements_over_a_year_ago:
                latest_annual_statement_over_a_year_ago = (
                    annual_statements_over_a_year_ago[-1]
                )

        latest_quarterly_statement_over_a_year_ago = None
        if ordered_quarterly_statements:
            quarterly_statements_over_a_year_ago = [
                quarterly_statement
                for quarterly_statement in ordered_quarterly_statements
                if quarterly_statement.date <= latest_statement_date - mininmum_time_ago
            ]

            if quarterly_statements_over_a_year_ago:
                latest_quarterly_statement_over_a_year_ago = (
                    quarterly_statements_over_a_year_ago[-1]
                )

        if (
            latest_annual_statement_over_a_year_ago
            and latest_quarterly_statement_over_a_year_ago
        ):
            return (
                latest_annual_statement_over_a_year_ago.statement
                if latest_annual_statement_over_a_year_ago.date
                >= latest_quarterly_statement_over_a_year_ago.date
                else latest_quarterly_statement_over_a_year_ago.statement
            )

        if latest_annual_statement_over_a_year_ago:
            return latest_annual_statement_over_a_year_ago.statement

        if latest_quarterly_statement_over_a_year_ago:
            return latest_quarterly_statement_over_a_year_ago.statement

        raise ValueError(
            f"Could not find any annual or quarterly {statement_name} statements from over a year ago."
        )

    def _get_ebit(self, income_statement: pd.Series) -> float:
        """
        Get EBIT from income statement using multiple fallback strategies.

        Args:
            income_statement: Income statement series from yfinance

        Returns:
            EBIT value as float

        Raises:
            ValueError: If EBIT cannot be obtained through any strategy
        """
        # Strategy 1: Direct access to EBIT field
        if "EBIT" in income_statement.index:
            return float(income_statement["EBIT"])

        # Strategy 2: Try "Operating Income" as alternative
        if "Operating Income" in income_statement.index:
            logger.warning("Using fallback strategy for EBIT: Operating Income")
            return float(income_statement["Operating Income"])

        # Strategy 3: Calculate from Net Income + Interest Expense + Tax Provision
        required_fields = ["Net Income", "Interest Expense", "Tax Provision"]
        if all(field in income_statement.index for field in required_fields):
            logger.warning(
                "Using fallback strategy for EBIT: Calculated from Net Income + Interest + Tax"
            )
            net_income = income_statement["Net Income"]
            interest_expense = income_statement["Interest Expense"]
            tax_provision = income_statement["Tax Provision"]
            # EBIT = Net Income + Interest Expense + Taxes
            return float(net_income + interest_expense + tax_provision)

        # If all strategies fail, raise an error
        available_fields = income_statement.index.tolist()
        raise ValueError(
            f"Could not retrieve EBIT from income statement. "
            f"Available fields: {available_fields}"
        )

    def _get_capital_expenditure(self, cash_flow: pd.Series) -> float:
        """
        Get Capital Expenditure from cash flow using multiple fallback strategies.

        Args:
            cash_flow: Cash flow series from yfinance

        Returns:
            Capital Expenditure value as float

        Raises:
            ValueError: If Capital Expenditure cannot be obtained through any strategy
        """
        # Strategy 1: Direct access to Capital Expenditure field
        if "Capital Expenditure" in cash_flow.index:
            return float(cash_flow["Capital Expenditure"])

        # Strategy 2: Try various alternative names
        alternatives = [
            "Purchase Of PPE",
            "Capital Expenditures",
            "Payments For Property Plant And Equipment",
            "Net PPE Purchase And Sale",
            "Purchase Of Property Plant And Equipment",
        ]
        for alternative in alternatives:
            if alternative in cash_flow.index:
                logger.warning(
                    f"Using fallback strategy for Capital Expenditure: {alternative}"
                )
                value = float(cash_flow[alternative])
                # Capex is typically negative in cash flow, ensure it's negative
                return value if value < 0 else -abs(value)

        # If all strategies fail, raise an error
        available_fields = cash_flow.index.tolist()
        raise ValueError(
            f"Could not retrieve Capital Expenditure from cash flow statement. "
            f"Available fields: {available_fields}"
        )

    def _get_interest_expense(self, income_statement: pd.Series) -> float:
        """
        Get Interest Expense from income statement using multiple fallback strategies.

        Args:
            income_statement: Income statement series from yfinance

        Returns:
            Interest Expense value as float

        Raises:
            ValueError: If Interest Expense cannot be obtained through any strategy
        """
        # Strategy 1: Direct access to Interest Expense field
        if "Interest Expense" in income_statement.index:
            return float(income_statement["Interest Expense"])

        # Strategy 2: Try alternative names
        for alternative in [
            "Interest Expense Non Operating",
            "Interest And Debt Expense",
        ]:
            if alternative in income_statement.index:
                logger.warning(
                    f"Using fallback strategy for Interest Expense: {alternative}"
                )
                return float(income_statement[alternative])

        # If all strategies fail, raise an error
        available_fields = income_statement.index.tolist()
        raise ValueError(
            f"Could not retrieve Interest Expense from income statement. "
            f"Available fields: {available_fields}"
        )

    def _get_total_debt(self, balance_sheet: pd.Series) -> float:
        """
        Get Total Debt from balance sheet using multiple fallback strategies.

        Args:
            balance_sheet: Balance sheet series from yfinance

        Returns:
            Total Debt value as float

        Raises:
            ValueError: If Total Debt cannot be obtained through any strategy
        """
        # Strategy 1: Direct access to Total Debt field
        if "Total Debt" in balance_sheet.index:
            return float(balance_sheet["Total Debt"])

        # Strategy 2: Calculate from Long Term Debt + Current Debt
        if (
            "Long Term Debt" in balance_sheet.index
            and "Current Debt" in balance_sheet.index
        ):
            logger.warning(
                "Using fallback strategy for Total Debt: Long Term Debt + Current Debt"
            )
            long_term_debt = balance_sheet["Long Term Debt"]
            current_debt = balance_sheet["Current Debt"]
            return float(long_term_debt + current_debt)

        # Strategy 3: Try just Long Term Debt if available
        if "Long Term Debt" in balance_sheet.index:
            logger.warning(
                "Using fallback strategy for Total Debt: Long Term Debt only"
            )
            return float(balance_sheet["Long Term Debt"])

        # Strategy 4: Try Current Debt alone
        if "Current Debt" in balance_sheet.index:
            logger.warning("Using fallback strategy for Total Debt: Current Debt only")
            return float(balance_sheet["Current Debt"])

        # If all strategies fail, raise an error
        available_fields = balance_sheet.index.tolist()
        raise ValueError(
            f"Could not retrieve Total Debt from balance sheet. "
            f"Available fields: {available_fields}"
        )

    def _get_beta(self, stock_info: dict[str, Any]) -> float:
        """
        Get beta from stock info.

        Args:
            stock_info: Stock info dictionary from yfinance

        Returns:
            Beta value as float

        Raises:
            ValueError: If beta cannot be obtained
        """
        # Try to get beta from stock info
        if "beta" in stock_info and stock_info["beta"] is not None:
            return float(stock_info["beta"])

        # If beta is not available, raise an error
        available_keys = list(stock_info.keys())
        raise ValueError(
            f"Could not retrieve beta from stock info. Available keys: {available_keys}"
        )

    def fetch_stock_data(self, ticker: str) -> StockData:
        stock_data = yf.Ticker(ticker)

        income_statement_dates = [
            pd_timestamp
            for pd_timestamp in cast(
                list[pd.Timestamp],
                stock_data.income_stmt.columns.to_list()
                + stock_data.quarterly_income_stmt.columns.to_list(),
            )
        ]
        balance_sheet_statement_dates = [
            pd_timestamp
            for pd_timestamp in cast(
                list[pd.Timestamp],
                stock_data.balance_sheet.columns.to_list()
                + stock_data.balance_sheet.columns.to_list(),
            )
        ]
        cash_flow_statement_dates = [
            pd_timestamp
            for pd_timestamp in cast(
                list[pd.Timestamp],
                stock_data.cash_flow.columns.to_list()
                + stock_data.cash_flow.columns.to_list(),
            )
        ]
        statement_date_set = set(income_statement_dates).intersection(
            set(balance_sheet_statement_dates), set(cash_flow_statement_dates)
        )

        # Try strict alignment first
        if len(statement_date_set) > 0:
            latest_statement_date = max(statement_date_set)
        else:
            logger.warning(
                f"No strict alignment found for {ticker}. Using 90-day window strategy."
            )
            # If no exact match, find statements within a reasonable window (90 days)
            # Use the most recent income statement date as the reference
            all_dates_combined = set(
                income_statement_dates
                + balance_sheet_statement_dates
                + cash_flow_statement_dates
            )
            latest_statement_date = None

            if len(all_dates_combined) == 0:
                raise ValueError(
                    "Could not find any financial statements (income statement, balance sheet, or cash flow)."
                )

            # Sort all dates to find the most recent
            sorted_dates = sorted(all_dates_combined, reverse=True)

            # Try to find a date that has all three statements within 90 days
            for candidate_date in sorted_dates:
                # Check if we have all three statement types within 90 days of this date
                window_start = candidate_date - timedelta(
                    days=STATEMENT_DATE_WINDOW_DAYS
                )
                window_end = candidate_date + timedelta(days=STATEMENT_DATE_WINDOW_DAYS)

                has_income = any(
                    window_start <= d <= window_end for d in income_statement_dates
                )
                has_balance = any(
                    window_start <= d <= window_end
                    for d in balance_sheet_statement_dates
                )
                has_cashflow = any(
                    window_start <= d <= window_end for d in cash_flow_statement_dates
                )

                if has_income and has_balance and has_cashflow:
                    # Use the most recent income statement date within the window
                    matching_income_dates = [
                        d
                        for d in income_statement_dates
                        if window_start <= d <= window_end
                    ]
                    latest_statement_date = max(matching_income_dates)
                    break

            if not latest_statement_date:
                raise ValueError(
                    "Could not find an income statement, a balance sheet, and a cash flow statement "
                    "all released within a reasonable time window (90 days)."
                )

        if latest_statement_date in stock_data.income_stmt.columns:
            income_statement = stock_data.income_stmt[latest_statement_date]
        else:
            income_statement = stock_data.quarterly_income_stmt[latest_statement_date]

        if latest_statement_date in stock_data.balance_sheet.columns:
            balance_sheet = stock_data.balance_sheet[latest_statement_date]
        elif latest_statement_date in stock_data.quarterly_balance_sheet.columns:
            balance_sheet = stock_data.quarterly_balance_sheet[latest_statement_date]
        else:
            # Find the closest balance sheet within 90 days
            window_start = latest_statement_date - timedelta(
                days=STATEMENT_DATE_WINDOW_DAYS
            )
            window_end = latest_statement_date + timedelta(
                days=STATEMENT_DATE_WINDOW_DAYS
            )
            matching_balance_dates = [
                d
                for d in balance_sheet_statement_dates
                if window_start <= d <= window_end
            ]
            if not matching_balance_dates:
                raise ValueError(
                    f"Could not find a balance sheet within 90 days of {latest_statement_date}"
                )
            closest_balance_date = min(
                matching_balance_dates,
                key=lambda d: abs((d - latest_statement_date).days),
            )
            logger.warning(
                f"Using closest balance sheet date {closest_balance_date} for {latest_statement_date}"
            )
            if closest_balance_date in stock_data.balance_sheet.columns:
                balance_sheet = stock_data.balance_sheet[closest_balance_date]
            else:
                balance_sheet = stock_data.quarterly_balance_sheet[closest_balance_date]

        if latest_statement_date in stock_data.cash_flow.columns:
            cash_flow = stock_data.cash_flow[latest_statement_date]
        elif latest_statement_date in stock_data.quarterly_cash_flow.columns:
            cash_flow = stock_data.quarterly_cash_flow[latest_statement_date]
        else:
            # Find the closest cash flow within 90 days
            window_start = latest_statement_date - timedelta(
                days=STATEMENT_DATE_WINDOW_DAYS
            )
            window_end = latest_statement_date + timedelta(
                days=STATEMENT_DATE_WINDOW_DAYS
            )
            matching_cashflow_dates = [
                d for d in cash_flow_statement_dates if window_start <= d <= window_end
            ]
            if not matching_cashflow_dates:
                raise ValueError(
                    f"Could not find a cash flow statement within 90 days of {latest_statement_date}"
                )
            closest_cashflow_date = min(
                matching_cashflow_dates,
                key=lambda d: abs((d - latest_statement_date).days),
            )
            logger.warning(
                f"Using closest cash flow date {closest_cashflow_date} for {latest_statement_date}"
            )
            if closest_cashflow_date in stock_data.cash_flow.columns:
                cash_flow = stock_data.cash_flow[closest_cashflow_date]
            else:
                cash_flow = stock_data.quarterly_cash_flow[closest_cashflow_date]

        last_years_balance_sheet = self._get_last_years_statement(
            latest_statement_pd_timestamp=latest_statement_date,
            annual_statements=stock_data.balance_sheet,
            quarterly_statements=stock_data.quarterly_balance_sheet,
            statement_name="balance sheet",
        )

        stock_data_info = cast(dict[str, Any] | None, stock_data.info)  # pyright: ignore[reportUnknownMemberType]

        return StockData(
            ebit=self._get_ebit(income_statement),
            revenue=income_statement["Total Revenue"],
            capital_expenditure=self._get_capital_expenditure(cash_flow),
            n_shares_outstanding=balance_sheet["Share Issued"],
            market_cap=cast(float, stock_data_info["marketCap"]),
            gross_debt=self._get_total_debt(balance_sheet),
            gross_debt_last_year=self._get_total_debt(last_years_balance_sheet),
            net_debt=self._get_total_debt(balance_sheet)
            - balance_sheet["Cash And Cash Equivalents"],
            total_interest_expense=self._get_interest_expense(income_statement),
            beta=self._get_beta(stock_data_info),
        )
