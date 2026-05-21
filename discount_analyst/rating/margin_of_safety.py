"""Pre-DCF margin-of-safety verdict derived from base-case intrinsic vs price."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import AliasChoices, BaseModel, Field
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
    """Quantitative margin-of-safety view anchored on the DCF base intrinsic."""

    current_price: float = Field(gt=0)
    intrinsic_value_base: float = Field(
        gt=0,
        validation_alias=AliasChoices("intrinsic_value_base", "base_intrinsic_value"),
        serialization_alias="intrinsic_value_base",
    )

    @classmethod
    def from_market_cap(
        cls,
        *,
        market_cap: float,
        n_shares_outstanding: float,
        intrinsic_value_base: float,
    ) -> Self:
        """Derive per-share price from market cap and shares; reject non-positive share count."""
        if n_shares_outstanding <= 0:
            msg = f"n_shares_outstanding must be positive, got {n_shares_outstanding}."
            raise ValueError(msg)
        return cls(
            current_price=market_cap / n_shares_outstanding,
            intrinsic_value_base=intrinsic_value_base,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def intrinsic_value_bear(self) -> float:
        # TODO: CODE-35 Use a dynamic bear case
        return self.intrinsic_value_base * 0.70

    @computed_field  # type: ignore[prop-decorator]
    @property
    def intrinsic_value_bull(self) -> float:
        # TODO: CODE-35 Use a dynamic bull case
        return self.intrinsic_value_base * 1.40

    @computed_field  # type: ignore[prop-decorator]
    @property
    def margin_of_safety_base_pct(self) -> float:
        return (
            (self.intrinsic_value_base - self.current_price) / self.current_price * 100
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
