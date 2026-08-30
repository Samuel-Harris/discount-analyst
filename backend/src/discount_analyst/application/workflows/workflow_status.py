"""Pure workflow-status derivation from Surveyor, Allocator, and ticker-lane statuses."""

from __future__ import annotations

from typing import Literal

WorkflowStatusName = Literal["running", "completed", "failed", "cancelled"]

_ACTIVE_EXECUTION = frozenset({"pending", "running"})
_TERMINAL_RUN = frozenset({"completed", "failed", "cancelled"})


def derive_workflow_status(
    *,
    surveyor_status: str | None,
    allocator_status: str | None,
    run_statuses: tuple[str, ...],
) -> WorkflowStatusName:
    """Return the workflow status implied by child rows.

    Sticky cancellation and sticky failed-with-error are applied by the caller
    before this helper. Allocator ``pending`` or ``running`` keeps a
    lane-successful workflow running. A failed or cancelled lane makes the
    workflow failed or cancelled regardless of Allocator. A legacy skipped
    Allocator with completed lanes keeps the historical completed status.
    """
    if surveyor_status is None:
        return "running"
    if surveyor_status == "failed":
        return "failed"
    if surveyor_status == "cancelled":
        return "cancelled"
    if surveyor_status in _ACTIVE_EXECUTION:
        return "running"

    if run_statuses:
        if "running" in run_statuses:
            return "running"
        if "failed" in run_statuses:
            return "failed"
        if all(status == "completed" for status in run_statuses):
            return _status_after_successful_lanes(allocator_status)
        if all(status in _TERMINAL_RUN for status in run_statuses):
            return "cancelled"
        return "running"

    return _status_after_successful_lanes(allocator_status)


def _status_after_successful_lanes(
    allocator_status: str | None,
) -> WorkflowStatusName:
    if allocator_status is None or allocator_status in _ACTIVE_EXECUTION:
        return "running"
    if allocator_status == "completed":
        return "completed"
    if allocator_status == "failed":
        return "failed"
    if allocator_status == "cancelled":
        return "cancelled"
    if allocator_status == "skipped":
        return "completed"
    return "running"
