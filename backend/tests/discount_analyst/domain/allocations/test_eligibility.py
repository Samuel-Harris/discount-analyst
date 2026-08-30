"""Tests for Verdict-to-allocation-policy mapping."""

import pytest

from discount_analyst.domain.allocations.eligibility import allocation_policy_for
from discount_analyst.domain.allocations.policy import (
    ForcedZeroPolicy,
    ForcedZeroReason,
    InvestablePolicy,
    RetainOrReducePolicy,
)
from discount_analyst.domain.decisions.investment_rating import InvestmentRating


@pytest.mark.parametrize(
    "rating",
    [InvestmentRating.BUY, InvestmentRating.STRONG_BUY],
)
def test_buy_ratings_are_investable(rating: InvestmentRating) -> None:
    policy = allocation_policy_for(
        rating=rating,
        is_existing_position=False,
        current_weight_pct=0.0,
    )

    assert policy == InvestablePolicy()


def test_existing_hold_is_retain_or_reduce() -> None:
    policy = allocation_policy_for(
        rating=InvestmentRating.HOLD,
        is_existing_position=True,
        current_weight_pct=8.5,
    )

    assert policy == RetainOrReducePolicy(current_weight_pct=8.5)


def test_new_hold_is_forced_zero() -> None:
    policy = allocation_policy_for(
        rating=InvestmentRating.HOLD,
        is_existing_position=False,
        current_weight_pct=0.0,
    )

    assert policy == ForcedZeroPolicy(reason=ForcedZeroReason.NEW_HOLD)


def test_sell_is_forced_zero_for_existing_and_new() -> None:
    existing = allocation_policy_for(
        rating=InvestmentRating.SELL,
        is_existing_position=True,
        current_weight_pct=12.0,
    )
    new = allocation_policy_for(
        rating=InvestmentRating.SELL,
        is_existing_position=False,
        current_weight_pct=0.0,
    )

    assert existing == ForcedZeroPolicy(reason=ForcedZeroReason.SELL)
    assert new == ForcedZeroPolicy(reason=ForcedZeroReason.SELL)


def test_strong_sell_is_forced_zero() -> None:
    policy = allocation_policy_for(
        rating=InvestmentRating.STRONG_SELL,
        is_existing_position=True,
        current_weight_pct=5.0,
    )

    assert policy == ForcedZeroPolicy(reason=ForcedZeroReason.STRONG_SELL)
