from enum import Enum
import enum
from pydantic import BaseModel
import pytest
from discount_analyst.data_fetcher import DataFetcher


@enum.unique
class Region(Enum):
    US = enum.auto()
    UK = enum.auto()


@enum.unique
class Size(Enum):
    MICRO = enum.auto()
    SMALL = enum.auto()
    MID = enum.auto()
    LARGE = enum.auto()


class TestCase(BaseModel):
    ticker_symbol: str
    region: Region
    size: Size


TEST_CASES: list[TestCase] = [
    # Large cap US ($10B <)
    TestCase(ticker_symbol="MSFT", region=Region.US, size=Size.LARGE),
    TestCase(ticker_symbol="AMD", region=Region.US, size=Size.LARGE),
    TestCase(ticker_symbol="GS", region=Region.US, size=Size.LARGE),
    TestCase(ticker_symbol="PFE", region=Region.US, size=Size.LARGE),
    # Mid cap US ($2B - $10B)
    TestCase(ticker_symbol="STWD", region=Region.US, size=Size.MID),
    TestCase(ticker_symbol="JDSPY", region=Region.US, size=Size.MID),
    TestCase(ticker_symbol="ORI", region=Region.US, size=Size.MID),
    TestCase(ticker_symbol="CART", region=Region.US, size=Size.MID),
    # Small cap US ($250M - $2B)
    TestCase(ticker_symbol="CNECF", region=Region.US, size=Size.SMALL),
    TestCase(ticker_symbol="HLX", region=Region.US, size=Size.SMALL),
    TestCase(ticker_symbol="BYND", region=Region.US, size=Size.SMALL),
    TestCase(ticker_symbol="ASST", region=Region.US, size=Size.SMALL),
    # Micro cap US (< $250M)
    TestCase(ticker_symbol="STEM", region=Region.US, size=Size.MICRO),
    TestCase(ticker_symbol="FINR", region=Region.US, size=Size.MICRO),
    TestCase(ticker_symbol="TWOH", region=Region.US, size=Size.MICRO),
    TestCase(ticker_symbol="BURU", region=Region.US, size=Size.MICRO),
    # Large cap UK (£2.5B <)
    TestCase(ticker_symbol="AZN.L", region=Region.UK, size=Size.LARGE),
    TestCase(ticker_symbol="TSCO.L", region=Region.UK, size=Size.LARGE),
    TestCase(ticker_symbol="NWG.L", region=Region.UK, size=Size.LARGE),
    TestCase(ticker_symbol="VOD.L", region=Region.UK, size=Size.LARGE),
    # Mid cap UK (£350M - £2.5B)
    TestCase(ticker_symbol="GRG.L", region=Region.UK, size=Size.MID),
    TestCase(ticker_symbol="MOON.L", region=Region.UK, size=Size.MID),
    TestCase(ticker_symbol="MSMN.L", region=Region.UK, size=Size.MID),
    TestCase(ticker_symbol="KLSO.L", region=Region.UK, size=Size.MID),
    # Small cap UK (£50M - £350M)
    TestCase(ticker_symbol="GYM.L", region=Region.UK, size=Size.SMALL),
    TestCase(ticker_symbol="0K17.L", region=Region.UK, size=Size.SMALL),
    TestCase(ticker_symbol="EQT.L", region=Region.UK, size=Size.SMALL),
    TestCase(ticker_symbol="LEND.L", region=Region.UK, size=Size.SMALL),
    # Micro cap UK (< £50M)
    TestCase(ticker_symbol="0K17.L", region=Region.UK, size=Size.MICRO),
    TestCase(ticker_symbol="0VLY.L", region=Region.UK, size=Size.MICRO),
    TestCase(ticker_symbol="0JQ2.L", region=Region.UK, size=Size.MICRO),
    TestCase(ticker_symbol="0O0E.L", region=Region.UK, size=Size.MICRO),
]


@pytest.mark.yfinance
@pytest.mark.parametrize(
    "test_case",
    [
        pytest.param(
            test_case,
            id=f"{test_case.region} - {test_case.size} - {test_case.ticker_symbol}",
        )
        for test_case in TEST_CASES
    ],
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
