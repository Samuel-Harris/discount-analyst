"""Shared investment rating strings (schema, Arbiter, programmatic verdicts)."""

from enum import StrEnum


class InvestmentRating(StrEnum):
    """Five-level rating used by Arbiter and hoisted onto ``Verdict``."""

    STRONG_BUY = "STRONG BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG SELL"
