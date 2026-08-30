"""Derived rebalance action from current weight and the no-trade band."""

from enum import StrEnum


class RebalanceAction(StrEnum):
    ENTER = "enter"
    INCREASE = "increase"
    HOLD = "hold"
    REDUCE = "reduce"
    EXIT = "exit"
    AVOID = "avoid"


def derive_rebalance_action(
    *,
    current_weight_pct: float,
    target_weight_pct: float,
    acceptable_weight_low_pct: float,
    acceptable_weight_high_pct: float,
    is_existing_position: bool,
) -> RebalanceAction:
    """Derive the trade action without changing the numerical targets.

    Current weight inside the acceptable band is a no-trade. A new name with a
    zero target is ``avoid`` even when that zero sits inside the band.
    """
    inside_band = (
        acceptable_weight_low_pct <= current_weight_pct <= acceptable_weight_high_pct
    )
    if inside_band:
        if not is_existing_position and target_weight_pct == 0:
            return RebalanceAction.AVOID
        return RebalanceAction.HOLD
    if current_weight_pct < acceptable_weight_low_pct:
        if not is_existing_position:
            return RebalanceAction.ENTER
        return RebalanceAction.INCREASE
    if target_weight_pct == 0:
        return RebalanceAction.EXIT
    return RebalanceAction.REDUCE
