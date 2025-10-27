from pydantic import BaseModel, ConfigDict
from datetime import date
import pandas as pd


class StockData(BaseModel):
    ebit: float
    revenue: float
    capital_expenditure: float
    n_shares_outstanding: float
    equity_value: float
    gross_debt: float
    gross_debt_last_year: float
    net_debt: float
    total_interest_expense: float
    beta: float


class Statement(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    date: date
    statement: pd.Series
