from pydantic import BaseModel
import pytest
from discount_analyst.data_fetcher import DataFetcher


class TestCase(BaseModel):
    ticker_symbol: str


TEST_CASES: list[TestCase] = [
    # Large cap US ($10B <)
    TestCase(ticker_symbol="MSFT"),
    TestCase(ticker_symbol="AMD"),
    # Mid cap US ($2B - $10B)
    TestCase(ticker_symbol="STWD"),
    TestCase(ticker_symbol="JDSPY"),
    # Small cap US ($250M - $2B)
    TestCase(ticker_symbol="CNECF"),
    TestCase(ticker_symbol="HLX"),
    # Micro cap US (< $250M)
    TestCase(ticker_symbol="STEM"),
    TestCase(ticker_symbol="FINR"),
    # Large cap UK (£2.5B <)
    TestCase(ticker_symbol="AZN.L"),
    TestCase(ticker_symbol="TSCO.L"),
    # Mid cap UK (£350M - £2.5B)
    TestCase(ticker_symbol="GRG.L"),
    TestCase(ticker_symbol="MOON.L"),
    # Small cap UK (£50M - £350M)
    TestCase(ticker_symbol="GYM.L"),
    TestCase(ticker_symbol="0K17.L"),
    # Micro cap UK (< £50M)
    TestCase(ticker_symbol="0K17.L"),
    TestCase(ticker_symbol="0VLY.L"),
]


@pytest.mark.yfinance
@pytest.mark.parametrize(
    "test_case",
    [pytest.param(test_case, id=test_case.ticker_symbol) for test_case in TEST_CASES],
)
def test_fetch_stock_data(test_case: TestCase):
    # Given
    data_fetcher = DataFetcher()

    # When
    actual_stock_data = data_fetcher.fetch_stock_data(test_case.ticker_symbol)

    # Then
    assert actual_stock_data.ebit != 0
    assert actual_stock_data.revenue != 0
    assert actual_stock_data.capital_expenditure != 0
    assert actual_stock_data.n_shares_outstanding != 0
    assert actual_stock_data.equity_value != 0
    assert actual_stock_data.gross_debt != 0
    assert actual_stock_data.gross_debt_last_year != 0
    assert actual_stock_data.net_debt != 0
    assert actual_stock_data.total_interest_expense != 0
    assert actual_stock_data.beta != 0
