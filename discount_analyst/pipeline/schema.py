from typing import Literal

from pydantic import BaseModel, Field

from discount_analyst.agents.arbiter.schema import ArbiterDecision
from discount_analyst.rating import InvestmentRating

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


class Verdict(BaseModel):
    """Unified human-facing output; ``decision`` type encodes Sentinel vs Arbiter."""

    ticker: str
    company_name: str
    decision_date: str
    is_existing_position: bool

    rating: InvestmentRating
    recommended_action: str

    decision: ArbiterDecision | SentinelRejection
