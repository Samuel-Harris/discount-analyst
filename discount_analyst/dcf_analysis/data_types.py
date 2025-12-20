from pydantic import BaseModel

from discount_analyst.shared.data_types import StockAssumptions, StockData


class DCFAnalysisParameters(BaseModel):
    stock_data: StockData
    stock_assumptions: StockAssumptions

    risk_free_rate: float
    expected_market_return: float = 0.09


class DCFAnalysisResult(BaseModel):
    intrinsic_share_price: float
    enterprise_value: float
    equity_value: float
