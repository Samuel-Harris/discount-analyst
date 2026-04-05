from pydantic import BaseModel, Field

from discount_analyst.agents.surveyor.schema import SurveyorCandidate


class ProfilerOutput(BaseModel):
    """Structured output from a single Profiler run (one ticker)."""

    candidate: SurveyorCandidate = Field(
        description=(
            "The fully populated candidate record for this ticker, "
            "structurally identical to a Surveyor candidate row."
        ),
    )
