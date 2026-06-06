from typing import Literal

from pydantic import BaseModel, Field

from discount_analyst.rating.investment_rating import InvestmentRating
from discount_analyst.rating.margin_of_safety import MarginOfSafetyAssessment

SentinelRejectionRating = Literal[
    InvestmentRating.SELL,
    InvestmentRating.STRONG_SELL,
]


class SentinelRejection(BaseModel):
    """Programmatic rejection when Sentinel blocks valuation (short-circuit path)."""

    ticker: str
    company_name: str
    decision_date: str
    is_existing_position: bool

    rating: SentinelRejectionRating
    recommended_action: str
    rejection_reason: str = Field(
        description="Plain-language statement of thesis and/or red-flag triggers."
    )


class RatingTableRationale(BaseModel):
    """Structured rationale fields persisted with the rating-table decision."""

    primary_driver: str
    supporting_factors: list[str] = Field(default_factory=list)
    mitigating_factors: list[str] = Field(default_factory=list)
    red_flag_disposition: str
    data_gap_disposition: str


class RatingTableDecision(BaseModel):
    """Deterministic valuation-gated rating built from Appraiser distribution."""

    decision_rule_id: Literal["rating_table_v1"]
    ticker: str
    company_name: str
    decision_date: str
    is_existing_position: bool

    rating: InvestmentRating
    recommended_action: str
    conviction: Literal["Low", "Medium", "High"]
    margin_of_safety: MarginOfSafetyAssessment

    rationale: RatingTableRationale
    thesis_expiry_note: str


class Verdict(BaseModel):
    """Unified human-facing output; ``decision`` encodes Sentinel vs rating-table path."""

    ticker: str
    company_name: str
    decision_date: str
    is_existing_position: bool

    rating: InvestmentRating
    recommended_action: str

    decision: RatingTableDecision | SentinelRejection
