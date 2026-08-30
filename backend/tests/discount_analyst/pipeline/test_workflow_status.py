"""Tests for workflow status derivation including the Allocator barrier."""

from discount_analyst.application.workflows.workflow_status import (
    derive_workflow_status,
)


def test_allocator_pending_keeps_successful_lanes_running() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="completed",
            allocator_status="pending",
            run_statuses=("completed", "completed"),
        )
        == "running"
    )


def test_allocator_completed_completes_workflow() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="completed",
            allocator_status="completed",
            run_statuses=("completed",),
        )
        == "completed"
    )


def test_failed_lane_fails_workflow_even_if_allocator_pending() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="completed",
            allocator_status="pending",
            run_statuses=("completed", "failed"),
        )
        == "failed"
    )


def test_skipped_allocator_with_completed_lanes_is_legacy_completed() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="completed",
            allocator_status="skipped",
            run_statuses=("completed",),
        )
        == "completed"
    )


def test_empty_lanes_wait_for_allocator() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="completed",
            allocator_status="pending",
            run_statuses=(),
        )
        == "running"
    )


def test_allocator_failed_fails_workflow_after_successful_lanes() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="completed",
            allocator_status="failed",
            run_statuses=("completed",),
        )
        == "failed"
    )


def test_surveyor_failed_fails_workflow() -> None:
    assert (
        derive_workflow_status(
            surveyor_status="failed",
            allocator_status="pending",
            run_statuses=(),
        )
        == "failed"
    )
