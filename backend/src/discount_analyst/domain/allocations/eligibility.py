"""Map a lane rating onto allocation authority."""

from discount_analyst.domain.allocations.policy import (
    AllocationPolicy,
    ForcedZeroPolicy,
    ForcedZeroReason,
    InvestablePolicy,
    RetainOrReducePolicy,
)
from discount_analyst.domain.decisions.investment_rating import InvestmentRating


def allocation_policy_for(
    *,
    rating: InvestmentRating,
    is_existing_position: bool,
    current_weight_pct: float,
) -> AllocationPolicy:
    """Return the canonical allocation permission for a completed lane.

    ``BUY`` and ``STRONG BUY`` are investable. Existing ``HOLD`` may only
    retain or reduce. New ``HOLD``, ``SELL``, and ``STRONG SELL`` are forced
    to zero. Data-quality and Sentinel rejections inherit this mapping through
    their existing ratings.
    """
    if rating in (InvestmentRating.BUY, InvestmentRating.STRONG_BUY):
        return InvestablePolicy()
    if rating == InvestmentRating.HOLD:
        if is_existing_position:
            return RetainOrReducePolicy(current_weight_pct=current_weight_pct)
        return ForcedZeroPolicy(reason=ForcedZeroReason.NEW_HOLD)
    if rating == InvestmentRating.SELL:
        return ForcedZeroPolicy(reason=ForcedZeroReason.SELL)
    if rating == InvestmentRating.STRONG_SELL:
        return ForcedZeroPolicy(reason=ForcedZeroReason.STRONG_SELL)
    raise ValueError(f"Unsupported investment rating: {rating!r}")
