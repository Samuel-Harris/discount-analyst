"""Deterministic rating mapping (MoS bucket × conviction × Sentinel reservations).

``recommended_action`` text follows the Arbiter-era framing table (new vs existing),
with short parenthetical tags so ``InvestmentRating`` can strip them where needed.
"""

from __future__ import annotations

from typing import Literal

from discount_analyst.rating.investment_rating import InvestmentRating
from discount_analyst.rating.margin_of_safety import MarginOfSafetyVerdict

ConvictionLevel = Literal["Low", "Medium", "High"]


def _investment_rating_for_matrix(
    margin_of_safety_verdict: MarginOfSafetyVerdict,
    conviction: ConvictionLevel,
    sentinel_has_reservations: bool,
) -> InvestmentRating:
    """Flat ``match`` on ``(MoS, conviction, reservations)``; ``assert_never`` on the tail."""

    match (
        margin_of_safety_verdict,
        conviction,
        sentinel_has_reservations,
    ):
        case (
            "Substantial — price implies significant downside in market expectations",
            "High",
            False,
        ):
            return InvestmentRating.STRONG_BUY
        case (
            "Substantial — price implies significant downside in market expectations",
            _,
            _,
        ):
            return InvestmentRating.BUY
        case (
            "Moderate — meaningful upside but not exceptional",
            "High" | "Medium",
            _,
        ):
            return InvestmentRating.BUY
        case (
            "Moderate — meaningful upside but not exceptional",
            "Low",
            _,
        ):
            return InvestmentRating.HOLD
        case ("Thin — limited margin for error", _, _):
            return InvestmentRating.HOLD
        case ("None — stock appears fairly valued or overvalued", _, _):
            return InvestmentRating.SELL


def _recommended_action_for_rating_position(
    rating: InvestmentRating,
    is_existing_position: bool,
) -> str:
    """Flat ``match`` on ``(rating, is_existing_position)``; ``assert_never`` on the tail."""
    match (rating, is_existing_position):
        case (InvestmentRating.STRONG_BUY, False):
            return "Initiate at full position (core sizing)"
        case (InvestmentRating.STRONG_BUY, True):
            return "Add to position (scale toward target)"
        case (InvestmentRating.BUY, False):
            return "Initiate at half or quarter position (starter)"
        case (InvestmentRating.BUY, True):
            return "Hold; consider adding if position is underweight (add)"
        case (InvestmentRating.HOLD, False):
            return "Does not clear the bar — do not initiate (pass)"
        case (InvestmentRating.HOLD, True):
            return "Thesis intact; valuation roughly fair; continue holding (monitor)"
        case (InvestmentRating.SELL, False):
            return "Stock is overvalued or thesis is broken — avoid (no new)"
        case (InvestmentRating.SELL, True):
            return "Exit the position (reduce)"
        case (InvestmentRating.STRONG_SELL, False):
            return "Serious concern; avoid (no new)"
        case (InvestmentRating.STRONG_SELL, True):
            return "Exit immediately (urgent)"


def rating_from_table_inputs(
    *,
    margin_of_safety_verdict: MarginOfSafetyVerdict,
    conviction: ConvictionLevel,
    sentinel_has_reservations: bool,
    is_existing_position: bool,
) -> tuple[InvestmentRating, str]:
    """Return ``(rating, recommended_action)`` for one valuation-gated decision row."""
    rating = _investment_rating_for_matrix(
        margin_of_safety_verdict,
        conviction,
        sentinel_has_reservations,
    )
    action = _recommended_action_for_rating_position(rating, is_existing_position)
    return rating, action
