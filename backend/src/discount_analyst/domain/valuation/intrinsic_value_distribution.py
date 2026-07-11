"""Method-agnostic intrinsic-value distribution (domain contract)."""

from pydantic import BaseModel, Field, model_validator


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
