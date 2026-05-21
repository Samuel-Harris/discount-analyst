"""Appraiser output plus deterministic DCF — valuation bundle for downstream rating."""

from pydantic import BaseModel

from discount_analyst.agents.appraiser.schema import AppraiserOutput
from discount_analyst.valuation.data_types import DCFAnalysisResult


class ValuationResult(BaseModel):
    """Appraiser output plus deterministic DCF — inputs for margin-of-safety and tables."""

    appraiser_output: AppraiserOutput
    dcf_result: DCFAnalysisResult
