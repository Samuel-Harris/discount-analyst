from pydantic import BaseModel

from discount_analyst.valuation.schema import StockAssumptions, StockData


class DCFAnalysisParameters(BaseModel):
    stock_data: StockData
    stock_assumptions: StockAssumptions

    risk_free_rate_pct: float
    expected_market_return_pct: float = 9.0


class DCFAnalysisResult(BaseModel):
    intrinsic_share_price: float
    enterprise_value: float
    equity_value: float
