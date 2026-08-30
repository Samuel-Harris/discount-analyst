"""Resolve the in-run live thesis from a Strategist keep/replace decision."""

from __future__ import annotations

from discount_analyst.agents.strategist.schema import (
    KeepPriorThesis,
    MispricingThesis,
    ReplaceThesis,
    StrategistDecision,
)


class KeepPriorWithoutThesisError(ValueError):
    """Raised when Strategist emits keep_prior but no prior thesis exists."""


def resolve_live_thesis(
    decision: StrategistDecision, prior: MispricingThesis | None
) -> MispricingThesis:
    """Return the live ``MispricingThesis`` for this run.

    Replace uses the nested thesis. Keep copies the prior object bit-for-bit.
    Keep with no prior is a lane failure.
    """
    match decision.root:
        case ReplaceThesis() as replace:
            return replace.thesis
        case KeepPriorThesis():
            if prior is None:
                msg = "keep_prior is invalid when no prior mispricing thesis exists."
                raise KeepPriorWithoutThesisError(msg)
            return prior.model_copy(deep=True)
