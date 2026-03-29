from pydantic import BaseModel

from discount_analyst.shared.models.data_types import StockAssumptions, StockData


class AppraiserOutput(BaseModel):
    stock_data: StockData
    stock_assumptions: StockAssumptions
