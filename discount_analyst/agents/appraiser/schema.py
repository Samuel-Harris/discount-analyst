from pydantic import BaseModel, Field

from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.sentinel.schema import EvaluationReport
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.valuation.schema import StockAssumptions, StockData


class AppraiserInput(BaseModel):
    """Structured input for the Appraiser (same upstream contract as the full workflow)."""

    stock_candidate: SurveyorCandidate
    deep_research: DeepResearchReport
    thesis: MispricingThesis
    evaluation: EvaluationReport
    risk_free_rate: float = Field(
        description=(
            "Risk-free rate as a decimal (e.g. 0.045). Supplied by the caller; "
            "must not be inferred by the model."
        ),
    )


class AppraiserOutput(BaseModel):
    """Structured output from the Appraiser agent (current snapshot + forward assumptions)."""

    stock_data: StockData
    stock_assumptions: StockAssumptions
