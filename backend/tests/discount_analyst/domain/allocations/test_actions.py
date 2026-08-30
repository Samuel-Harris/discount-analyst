"""Tests for no-trade-band rebalance actions."""

from discount_analyst.domain.allocations.actions import (
    RebalanceAction,
    derive_rebalance_action,
)


def test_current_weight_inside_band_is_hold() -> None:
    action = derive_rebalance_action(
        current_weight_pct=10.0,
        target_weight_pct=9.0,
        acceptable_weight_low_pct=8.0,
        acceptable_weight_high_pct=12.0,
        is_existing_position=True,
    )

    assert action is RebalanceAction.HOLD


def test_new_zero_inside_band_is_avoid() -> None:
    action = derive_rebalance_action(
        current_weight_pct=0.0,
        target_weight_pct=0.0,
        acceptable_weight_low_pct=0.0,
        acceptable_weight_high_pct=0.0,
        is_existing_position=False,
    )

    assert action is RebalanceAction.AVOID


def test_new_name_below_band_is_enter() -> None:
    action = derive_rebalance_action(
        current_weight_pct=0.0,
        target_weight_pct=8.0,
        acceptable_weight_low_pct=6.0,
        acceptable_weight_high_pct=10.0,
        is_existing_position=False,
    )

    assert action is RebalanceAction.ENTER


def test_existing_name_below_band_is_increase() -> None:
    action = derive_rebalance_action(
        current_weight_pct=4.0,
        target_weight_pct=8.0,
        acceptable_weight_low_pct=6.0,
        acceptable_weight_high_pct=10.0,
        is_existing_position=True,
    )

    assert action is RebalanceAction.INCREASE


def test_existing_name_above_band_is_reduce() -> None:
    action = derive_rebalance_action(
        current_weight_pct=12.0,
        target_weight_pct=6.0,
        acceptable_weight_low_pct=4.0,
        acceptable_weight_high_pct=8.0,
        is_existing_position=True,
    )

    assert action is RebalanceAction.REDUCE


def test_forced_zero_existing_above_band_is_exit() -> None:
    action = derive_rebalance_action(
        current_weight_pct=9.0,
        target_weight_pct=0.0,
        acceptable_weight_low_pct=0.0,
        acceptable_weight_high_pct=0.0,
        is_existing_position=True,
    )

    assert action is RebalanceAction.EXIT
