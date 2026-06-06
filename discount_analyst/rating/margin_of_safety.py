"""Margin-of-safety verdict derived from Appraiser expected intrinsic value."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import AliasChoices, BaseModel, Field, model_validator
from pydantic.fields import computed_field

MarginOfSafetyVerdict = Literal[
    "Substantial — price implies significant downside in market expectations",
    "Moderate — meaningful upside but not exceptional",
    "Thin — limited margin for error",
    "None — stock appears fairly valued or overvalued",
]

MOS_SUBSTANTIAL: MarginOfSafetyVerdict = (
    "Substantial — price implies significant downside in market expectations"
)
MOS_MODERATE: MarginOfSafetyVerdict = "Moderate — meaningful upside but not exceptional"
MOS_THIN: MarginOfSafetyVerdict = "Thin — limited margin for error"
MOS_NONE: MarginOfSafetyVerdict = "None — stock appears fairly valued or overvalued"


class MarginOfSafetyAssessment(BaseModel):
    """Quantitative margin-of-safety view anchored on expected intrinsic value."""

    current_price: float = Field(gt=0)
    expected_intrinsic_value: float = Field(
        gt=0,
        validation_alias=AliasChoices(
            "expected_intrinsic_value",
            "intrinsic_value_base",
            "base_intrinsic_value",
        ),
    )
    p10_intrinsic_value: float = Field(gt=0)
    p25_intrinsic_value: float = Field(gt=0)
    p50_intrinsic_value: float = Field(gt=0)
    p75_intrinsic_value: float = Field(gt=0)
    p90_intrinsic_value: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_percentiles(self) -> "MarginOfSafetyAssessment":
        values = [
            self.p10_intrinsic_value,
            self.p25_intrinsic_value,
            self.p50_intrinsic_value,
            self.p75_intrinsic_value,
            self.p90_intrinsic_value,
        ]
        if values != sorted(values):
            msg = "Intrinsic value percentiles must be monotonic."
            raise ValueError(msg)
        if (
            not self.p10_intrinsic_value
            <= self.expected_intrinsic_value
            <= self.p90_intrinsic_value
        ):
            msg = "expected_intrinsic_value must lie between p10 and p90."
            raise ValueError(msg)
        return self

    @classmethod
    def from_distribution(
        cls,
        *,
        current_price: float,
        expected_intrinsic_value: float,
        p10_intrinsic_value: float,
        p25_intrinsic_value: float,
        p50_intrinsic_value: float,
        p75_intrinsic_value: float,
        p90_intrinsic_value: float,
    ) -> Self:
        return cls(
            current_price=current_price,
            expected_intrinsic_value=expected_intrinsic_value,
            p10_intrinsic_value=p10_intrinsic_value,
            p25_intrinsic_value=p25_intrinsic_value,
            p50_intrinsic_value=p50_intrinsic_value,
            p75_intrinsic_value=p75_intrinsic_value,
            p90_intrinsic_value=p90_intrinsic_value,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def intrinsic_value_base(self) -> float:
        return self.expected_intrinsic_value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def intrinsic_value_bear(self) -> float:
        return self.p10_intrinsic_value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def intrinsic_value_bull(self) -> float:
        return self.p90_intrinsic_value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def margin_of_safety_base_pct(self) -> float:
        return (
            (self.expected_intrinsic_value - self.current_price)
            / self.current_price
            * 100
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def margin_of_safety_verdict(self) -> MarginOfSafetyVerdict:
        if self.margin_of_safety_base_pct >= 40:
            return MOS_SUBSTANTIAL
        if self.margin_of_safety_base_pct >= 20:
            return MOS_MODERATE
        if self.margin_of_safety_base_pct > 0:
            return MOS_THIN
        return MOS_NONE
