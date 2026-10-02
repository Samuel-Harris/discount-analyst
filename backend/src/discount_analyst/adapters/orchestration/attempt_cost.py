"""Map a pydantic-ai usage object onto a stored attempt cost."""

from __future__ import annotations

from pydantic_ai.usage import RunUsage

from discount_analyst.domain.workflow_cost import AttemptCost


def attempt_cost_from_usage(usage: RunUsage | None) -> AttemptCost | None:
    """Return spend for a model run. No requests means nothing to record."""
    if usage is None or usage.requests <= 0:
        return None
    return AttemptCost(cost_usd=usage.cost)
