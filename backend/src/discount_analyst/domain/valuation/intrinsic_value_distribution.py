"""Method-agnostic intrinsic-value distribution (domain contract)."""

from pydantic import BaseModel, Field, model_validator

from discount_analyst.domain.valuation.toolkit.scenarios import (
    weighted_expected_value,
    weighted_percentile,
)

_PROBABILITY_SUM_TOLERANCE_PP = 0.05
_PERCENTILE_POINTS = (
    (10, "p10_intrinsic_value"),
    (25, "p25_intrinsic_value"),
    (50, "p50_intrinsic_value"),
    (75, "p75_intrinsic_value"),
    (90, "p90_intrinsic_value"),
)


class ValueScenario(BaseModel):
    """One weighted per-share outcome inside an intrinsic-value distribution."""

    value_per_share: float = Field(gt=0)
    probability_pct: float = Field(gt=0, le=100)


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
    scenarios: list[ValueScenario] = Field(
        min_length=3,
        description=(
            "At least three scenarios. probability_pct values sum to 100. "
            "expected_intrinsic_value and each percentile must match these "
            "weights; they are not rewritten."
        ),
    )
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
        self._validate_scenarios()
        return self

    def _validate_scenarios(self) -> None:
        probability_total = sum(scenario.probability_pct for scenario in self.scenarios)
        if abs(probability_total - 100.0) > _PROBABILITY_SUM_TOLERANCE_PP:
            msg = (
                "Scenario probability_pct values must sum to 100 "
                f"(within {_PROBABILITY_SUM_TOLERANCE_PP} percentage points)."
            )
            raise ValueError(msg)
        payload = [scenario.model_dump() for scenario in self.scenarios]
        tolerance = max(0.01, 0.005 * self.current_share_price)
        weighted_expected = weighted_expected_value(payload)
        if abs(self.expected_intrinsic_value - weighted_expected) > tolerance:
            msg = (
                "expected_intrinsic_value must match the probability-weighted "
                f"scenarios (weighted={weighted_expected}, "
                f"expected={self.expected_intrinsic_value}, tolerance={tolerance})."
            )
            raise ValueError(msg)
        for percentile, field_name in _PERCENTILE_POINTS:
            weighted = weighted_percentile(payload, percentile)
            submitted = getattr(self, field_name)
            if abs(submitted - weighted) > tolerance:
                msg = (
                    f"{field_name} must match the scenario percentile "
                    f"(weighted={weighted}, submitted={submitted}, "
                    f"tolerance={tolerance})."
                )
                raise ValueError(msg)
