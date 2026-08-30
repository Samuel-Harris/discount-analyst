"""Tests for workflow status derivation including the Curator barrier."""

from discount_analyst.application.workflows.workflow_status import (
    derive_workflow_status,
)


def test_curator_pending_keeps_successful_lanes_running() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="completed",
            curator_status="pending",
            run_statuses=("completed", "completed"),
        )
        == "running"
    )


def test_curator_completed_completes_workflow() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="completed",
            curator_status="completed",
            run_statuses=("completed",),
        )
        == "completed"
    )


def test_failed_lane_fails_workflow_even_if_curator_pending() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="completed",
            curator_status="pending",
            run_statuses=("completed", "failed"),
        )
        == "failed"
    )


def test_skipped_curator_with_completed_lanes_is_legacy_completed() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="completed",
            curator_status="skipped",
            run_statuses=("completed",),
        )
        == "completed"
    )


def test_empty_lanes_wait_for_curator() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="completed",
            curator_status="pending",
            run_statuses=(),
        )
        == "running"
    )


def test_curator_failed_fails_workflow_after_successful_lanes() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="completed",
            curator_status="failed",
            run_statuses=("completed",),
        )
        == "failed"
    )


def test_surveyor_failed_fails_workflow() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="failed",
            curator_status="pending",
            run_statuses=(),
        )
        == "failed"
    )
