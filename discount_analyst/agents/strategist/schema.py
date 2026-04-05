from typing import Literal

from pydantic import BaseModel, Field


class MispricingThesis(BaseModel):
    """Falsifiable argument for why the market is wrong on a name."""

    ticker: str
    company_name: str

    mispricing_type: str = Field(
        description=(
            "Brief label for the category of mispricing, e.g. "
            "'Cyclical trough misread as structural decline', "
            "'Turnaround not yet visible in trailing metrics', "
            "'Hidden asset valued at zero by market'."
        )
    )
    market_belief: str = Field(
        description=(
            "A precise statement of what the market currently believes "
            "about this business and why that belief is embedded in the price. "
            "This should be grounded in the market_narrative from deep research."
        )
    )
    mispricing_argument: str = Field(
        description=(
            "The specific argument for why the market belief is wrong. "
            "Reference concrete evidence from the deep research. "
            "This must go beyond 'the stock looks cheap' — it must explain "
            "the mechanism by which the market has made an error."
        )
    )
    resolution_mechanism: str = Field(
        description=(
            "How the gap between price and intrinsic value closes. "
            "What process, catalyst, or convergence dynamic causes the "
            "market to revise its view? Over what approximate timeframe?"
        )
    )
    falsification_conditions: list[str] = Field(
        description=(
            "Explicit list of conditions that would prove this thesis wrong. "
            "Each entry should be a concrete, observable event or data point — "
            "not vague language. Minimum 3 entries."
        )
    )
    thesis_risks: list[str] = Field(
        description=(
            "The strongest arguments against this thesis. Written as if by "
            "a skeptical analyst who has read the same deep research and "
            "reached the opposite conclusion."
        )
    )
    evaluation_questions: list[str] = Field(
        description=(
            "The specific questions the Evaluation Agent must answer to "
            "confirm or break this thesis. These should be bespoke to this "
            "thesis — not a generic checklist. Minimum 5 questions."
        )
    )
    permanent_loss_scenarios: list[str] = Field(
        description=(
            "Concrete scenarios under which this investment results in "
            "permanent, unrecoverable capital loss. Required by the investing "
            "creed's risk test. Minimum 2 entries."
        )
    )
    conviction_level: Literal["Low", "Medium", "High"] = Field(
        description=(
            "Initial conviction level based on the strength of the thesis "
            "and quality of evidence available. Low = thesis is plausible "
            "but evidence is thin. High = thesis is clearly grounded in "
            "multiple concrete data points."
        )
    )
