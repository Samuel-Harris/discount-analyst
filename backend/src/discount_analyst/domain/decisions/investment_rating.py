"""Shared investment rating enum for programmatic verdicts and dashboards."""

from enum import StrEnum


class InvestmentRating(StrEnum):
    """Five-level rating used on ``Verdict`` and related persistence."""

    STRONG_BUY = "STRONG BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG SELL"
