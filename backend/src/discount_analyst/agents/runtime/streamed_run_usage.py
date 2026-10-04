"""Attach the RunUsage from a streamed attempt onto the exception that ends it."""

from __future__ import annotations

from pydantic_ai.usage import RunUsage

_USAGE_ATTR = "discount_analyst_streamed_run_usage"


def attach_streamed_run_usage(exc: BaseException, usage: RunUsage | None) -> None:
    """Record usage once. A later attach on the same exception is ignored."""
    if hasattr(exc, _USAGE_ATTR):
        return
    setattr(exc, _USAGE_ATTR, usage)


def streamed_run_usage(exc: BaseException) -> RunUsage | None:
    """Return usage attached to ``exc`` or its cause chain."""
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if hasattr(current, _USAGE_ATTR):
            usage = getattr(current, _USAGE_ATTR)
            return usage if isinstance(usage, RunUsage) else None
        current = current.__cause__
    return None
