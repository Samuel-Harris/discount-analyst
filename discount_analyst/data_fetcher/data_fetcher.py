from typing import Any, cast
import yfinance as yf  # pyright: ignore[reportMissingTypeStubs]
import pandas as pd
from datetime import timedelta

from discount_analyst.data_fetcher.constants import PREVIOUS_YEAR_DAYS_AGO_MIN_THRESHOLD
from discount_analyst.data_fetcher.data_types import Statement, StockData


class DataFetcher:
    def _get_ordered_statement_from_df(
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
        ordered_annual_statements = self._get_ordered_statement_from_df(
            annual_statements
        )
        ordered_quarterly_statements = self._get_ordered_statement_from_df(
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

        if len(statement_date_set) == 0:
            raise ValueError(
                "Could not find an income statement, a balance sheet, and a cash flow statement all released on the same day."
            )

        latest_statement_date = max(statement_date_set)

        if latest_statement_date in stock_data.income_stmt.columns:
            income_statement = stock_data.income_stmt[latest_statement_date]
        else:
            income_statement = stock_data.quarterly_income_stmt[latest_statement_date]

        if latest_statement_date in stock_data.balance_sheet.columns:
            balance_sheet = stock_data.balance_sheet[latest_statement_date]
        else:
            balance_sheet = stock_data.quarterly_balance_sheet[latest_statement_date]

        if latest_statement_date in stock_data.cash_flow.columns:
            cash_flow = stock_data.cash_flow[latest_statement_date]
        else:
            cash_flow = stock_data.quarterly_cash_flow[latest_statement_date]

        last_years_balance_sheet = self._get_last_years_statement(
            latest_statement_pd_timestamp=latest_statement_date,
            annual_statements=stock_data.balance_sheet,
            quarterly_statements=stock_data.quarterly_balance_sheet,
            statement_name="balance sheet",
        )

        stock_data_info = stock_data.info  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

        return StockData(
            ebit=income_statement["EBIT"],
            revenue=income_statement["Total Revenue"],
            capital_expenditure=cash_flow["Capital Expenditure"],
            n_shares_outstanding=balance_sheet["Share Issued"],
            equity_value=cast(float, stock_data_info["marketCap"]),
            gross_debt=balance_sheet["Total Debt"],
            gross_debt_last_year=last_years_balance_sheet["Total Debt"],
            net_debt=balance_sheet["Total Debt"]
            - balance_sheet["Cash And Cash Equivalents"],
            total_interest_expense=income_statement["Interest Expense"],
            beta=cast(float, stock_data_info["beta"]),
        )
