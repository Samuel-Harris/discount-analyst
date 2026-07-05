"""Appraiser valuation output bundle for downstream rating."""

from pydantic import BaseModel

from discount_analyst.agents.appraiser.schema import AppraiserOutput


class ValuationResult(BaseModel):
    """Appraiser output for margin-of-safety and rating-table inputs."""

    appraiser_output: AppraiserOutput
