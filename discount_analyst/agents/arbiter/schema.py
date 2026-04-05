from typing import Literal

from pydantic import BaseModel, Field

from discount_analyst.agents.appraiser.schema import AppraiserOutput
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.sentinel.schema import EvaluationReport
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.rating import InvestmentRating
from discount_analyst.valuation.data_types import DCFAnalysisResult


class ValuationResult(BaseModel):
    """Appraiser output plus deterministic DCF — primary quantitative input for Arbiter."""

    appraiser_output: AppraiserOutput
    dcf_result: DCFAnalysisResult


class ArbiterInput(BaseModel):
    """Structured input for the Arbiter synthesis agent."""

    stock_candidate: SurveyorCandidate
    deep_research: DeepResearchReport
    thesis: MispricingThesis
    evaluation: EvaluationReport
    valuation: ValuationResult
    risk_free_rate: float = Field(
        description=(
            "Risk-free rate as a decimal (e.g. 0.045). Supplied by the caller; "
            "must not be inferred by the model."
        ),
    )
    is_existing_position: bool = Field(
        description=(
            "True if this stock is currently held. Affects recommended_action "
            "framing only, not the analytical rating."
        ),
    )


MarginOfSafetyVerdict = Literal[
    "Substantial — price implies significant downside in market expectations",
    "Moderate — meaningful upside but not exceptional",
    "Thin — limited margin for error",
    "None — stock appears fairly valued or overvalued",
]


class MarginOfSafetyAssessment(BaseModel):
    current_price: float
    bear_intrinsic_value: float
    base_intrinsic_value: float
    bull_intrinsic_value: float
    margin_of_safety_base_pct: float
    margin_of_safety_verdict: MarginOfSafetyVerdict


class ArbiterRationale(BaseModel):
    primary_driver: str
    supporting_factors: list[str]
    mitigating_factors: list[str]
    red_flag_disposition: str
    data_gap_disposition: str


class ArbiterDecision(BaseModel):
    ticker: str
    company_name: str
    decision_date: str
    is_existing_position: bool

    rating: InvestmentRating
    recommended_action: str
    conviction: Literal["Low", "Medium", "High"]
    margin_of_safety: MarginOfSafetyAssessment
    rationale: ArbiterRationale
    thesis_expiry_note: str
