from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.sentinel.schema import EvaluationReport
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.surveyor.schema import SurveyorCandidate


class AppraiserInput(BaseModel):
    """Structured input for the Appraiser (same upstream contract as the full workflow)."""

    stock_candidate: SurveyorCandidate
    deep_research: DeepResearchReport
    thesis: MispricingThesis
    evaluation: EvaluationReport
    risk_free_rate_pct: float = Field(
        description=(
            "Risk-free rate as a percentage (e.g. 4.5 means 4.5%). Supplied by the "
            "caller; must not be inferred by the model."
        ),
    )


class ValuationMethod(StrEnum):
    DCF = "dcf"
    REVERSE_DCF = "reverse_dcf"
    COMPARABLE_MULTIPLES = "comparable_multiples"
    SUM_OF_PARTS = "sum_of_parts"
    ASSET_VALUE = "asset_value"
    UNIT_ECONOMICS = "unit_economics"
    SCENARIO_WEIGHTING = "scenario_weighting"
    MONTE_CARLO = "monte_carlo"
    OTHER = "other"


class IntrinsicValueDistribution(BaseModel):
    """Normalised per-share intrinsic value range produced by the Appraiser."""

    currency: str = Field(
        min_length=3,
        max_length=8,
        description="Currency for all per-share values, e.g. USD, GBP, or GBX.",
    )
    current_share_price: float = Field(gt=0)
    expected_intrinsic_value: float = Field(gt=0)
    p10_intrinsic_value: float = Field(gt=0)
    p25_intrinsic_value: float = Field(gt=0)
    p50_intrinsic_value: float = Field(gt=0)
    p75_intrinsic_value: float = Field(gt=0)
    p90_intrinsic_value: float = Field(gt=0)
    distribution_method: str = Field(
        description="How the percentiles and expected value were constructed."
    )
    distribution_reasoning: str = Field(
        description="Concise explanation of the distribution and key judgement calls."
    )

    @model_validator(mode="after")
    def validate_distribution(self) -> "IntrinsicValueDistribution":
        values = [
            self.p10_intrinsic_value,
            self.p25_intrinsic_value,
            self.p50_intrinsic_value,
            self.p75_intrinsic_value,
            self.p90_intrinsic_value,
        ]
        if values != sorted(values):
            msg = (
                "Intrinsic value percentiles must be monotonic: "
                "p10 <= p25 <= p50 <= p75 <= p90."
            )
            raise ValueError(msg)
        if not (
            self.p10_intrinsic_value
            <= self.expected_intrinsic_value
            <= self.p90_intrinsic_value
        ):
            msg = "expected_intrinsic_value must lie between p10 and p90."
            raise ValueError(msg)
        return self


class ValuationMethodResult(BaseModel):
    """Evidence summary for one valuation method used by the Appraiser."""

    method: ValuationMethod
    role: Literal["primary", "cross_check"]
    value_per_share: float | None = Field(default=None, gt=0)
    low_value_per_share: float | None = Field(default=None, gt=0)
    high_value_per_share: float | None = Field(default=None, gt=0)
    weight_pct: float | None = Field(default=None, ge=0, le=100)
    key_assumptions: list[str] = Field(default_factory=list)
    evidence_summary: list[str] = Field(default_factory=list)
    sanity_checks: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_value_range(self) -> "ValuationMethodResult":
        if (
            self.low_value_per_share is not None
            and self.high_value_per_share is not None
            and self.low_value_per_share > self.high_value_per_share
        ):
            msg = "low_value_per_share must be <= high_value_per_share."
            raise ValueError(msg)
        return self


class AppraiserOutput(BaseModel):
    """Method-agnostic structured valuation output from the Appraiser agent."""

    ticker: str
    company_name: str
    valuation_date: str
    summary: str
    valuation_distribution: IntrinsicValueDistribution
    methods: list[ValuationMethodResult]
    key_value_drivers: list[str] = Field(default_factory=list)
    downside_risks_to_value: list[str] = Field(default_factory=list)
    upside_drivers_to_value: list[str] = Field(default_factory=list)
    data_quality: Literal["High", "Medium", "Low"]
    caveats: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_methods(self) -> "AppraiserOutput":
        if not self.methods:
            msg = "AppraiserOutput must contain valuation methods."
            raise ValueError(msg)
        primary_count = sum(method.role == "primary" for method in self.methods)
        if primary_count != 1:
            msg = "AppraiserOutput must contain exactly one primary valuation method."
            raise ValueError(msg)
        cross_check_count = sum(method.role == "cross_check" for method in self.methods)
        if cross_check_count < 1:
            msg = "AppraiserOutput must contain at least one cross-check method."
            raise ValueError(msg)
        total_weight = sum(
            method.weight_pct
            for method in self.methods
            if method.weight_pct is not None
        )
        if total_weight > 100.0:
            msg = "Valuation method weights must not sum to more than 100%."
            raise ValueError(msg)
        return self
