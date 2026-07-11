"""Reverse-DCF helpers for implied expectation checks."""

from __future__ import annotations

from collections.abc import Callable


def implied_margin_of_safety_pct(
    *, current_share_price: float, intrinsic_value_per_share: float
) -> float:
    if current_share_price <= 0:
        msg = f"current_share_price must be positive, got {current_share_price}."
        raise ValueError(msg)
    return (intrinsic_value_per_share - current_share_price) / current_share_price * 100


def implied_cagr_pct(
    *, starting_value: float, ending_value: float, years: int
) -> float:
    if starting_value <= 0 or ending_value <= 0:
        raise ValueError("starting_value and ending_value must be positive.")
    if years <= 0:
        msg = f"years must be positive, got {years}."
        raise ValueError(msg)
    return ((ending_value / starting_value) ** (1 / years) - 1) * 100


def solve_required_growth_pct(
    *,
    target_share_price: float,
    value_for_growth_pct: Callable[[float], float],
    low_growth_pct: float = -20.0,
    high_growth_pct: float = 40.0,
    tolerance: float = 0.01,
    max_iterations: int = 100,
) -> dict[str, float]:
    """Solve the growth rate whose modelled value equals the current price."""
    if target_share_price <= 0:
        msg = f"target_share_price must be positive, got {target_share_price}."
        raise ValueError(msg)
    low_value = value_for_growth_pct(low_growth_pct)
    high_value = value_for_growth_pct(high_growth_pct)
    if low_value > high_value:
        msg = "value_for_growth_pct must be monotonic increasing over the search range."
        raise ValueError(msg)
    if not (low_value <= target_share_price <= high_value):
        msg = (
            "target_share_price is outside the value range implied by low_growth_pct "
            "and high_growth_pct."
        )
        raise ValueError(msg)

    low = low_growth_pct
    high = high_growth_pct
    midpoint = (low + high) / 2
    midpoint_value = value_for_growth_pct(midpoint)
    for _ in range(max_iterations):
        midpoint = (low + high) / 2
        midpoint_value = value_for_growth_pct(midpoint)
        if abs(midpoint_value - target_share_price) <= tolerance:
            break
        if midpoint_value < target_share_price:
            low = midpoint
        else:
            high = midpoint
    return {
        "required_growth_pct": midpoint,
        "modelled_value_per_share": midpoint_value,
        "target_share_price": target_share_price,
    }
