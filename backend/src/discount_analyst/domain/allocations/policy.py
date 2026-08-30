"""Allocation authority derived from a lane Verdict."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ForcedZeroReason(StrEnum):
    NEW_HOLD = "new_hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class InvestablePolicy(BaseModel):
    kind: Literal["investable"] = "investable"


class RetainOrReducePolicy(BaseModel):
    kind: Literal["retain_or_reduce"] = "retain_or_reduce"
    current_weight_pct: float = Field(ge=0, le=100)


class ForcedZeroPolicy(BaseModel):
    kind: Literal["forced_zero"] = "forced_zero"
    reason: ForcedZeroReason


AllocationPolicy = Annotated[
    InvestablePolicy | RetainOrReducePolicy | ForcedZeroPolicy,
    Field(discriminator="kind"),
]
