from pydantic import BaseModel

from discount_analyst.shared.schemas.stock import StockAssumptions, StockData


class AppraiserOutput(BaseModel):
    stock_data: StockData
    stock_assumptions: StockAssumptions
