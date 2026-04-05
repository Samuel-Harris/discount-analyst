from pydantic import BaseModel

from discount_analyst.valuation.schema import StockAssumptions, StockData


class AppraiserOutput(BaseModel):
    """Structured output from the Appraiser agent (current snapshot + forward assumptions)."""

    stock_data: StockData
    stock_assumptions: StockAssumptions
