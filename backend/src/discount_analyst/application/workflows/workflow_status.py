"""Pure workflow-status derivation from Surveyor, Curator, and ticker-lane statuses."""

from __future__ import annotations

from typing import Literal

WorkflowStatusName = Literal["running", "completed", "failed", "cancelled"]

_ACTIVE_EXECUTION = frozenset({"pending", "running"})
_TERMINAL_RUN = frozenset({"completed", "failed", "cancelled"})


def derive_workflow_status(
    *,
    surveyor_status: str | None,
    curator_status: str | None,
    run_statuses: tuple[str, ...],
) -> WorkflowStatusName:
    """Return the workflow status implied by child rows.

    Sticky cancellation and sticky failed-with-error are applied by the caller
    before this helper. Curator ``pending`` or ``running`` keeps a
    lane-successful workflow running. A failed or cancelled lane makes the
    workflow failed or cancelled regardless of Curator. A legacy skipped
    Curator with completed lanes keeps the historical completed status.
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
            return _status_after_successful_lanes(curator_status)
        if all(status in _TERMINAL_RUN for status in run_statuses):
            return "cancelled"
        return "running"

    return _status_after_successful_lanes(curator_status)


def _status_after_successful_lanes(
    curator_status: str | None,
) -> WorkflowStatusName:
    if curator_status is None or curator_status in _ACTIVE_EXECUTION:
        return "running"
    if curator_status == "completed":
        return "completed"
    if curator_status == "failed":
        return "failed"
    if curator_status == "cancelled":
        return "cancelled"
    if curator_status == "skipped":
        return "completed"
    return "running"
