import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { WorkflowRunDetailResponse } from "../api";
import { WorkflowRunDetailHeader } from "./WorkflowRunDetailHeader";

function makeDetail(
  overrides: Partial<WorkflowRunDetailResponse> = {},
): WorkflowRunDetailResponse {
  return {
    id: "wf-1",
    started_at: "2026-04-01T12:00:00Z",
    completed_at: null,
    status: "running",
    is_mock: false,
    error_message: null,
    surveyor_execution: null,
    runs: [],
    ...overrides,
  };
}

describe("WorkflowRunDetailHeader", () => {
  it("shows Cancel workflow only for running workflows", () => {
    const sharedProps = {
      onRequestDelete: vi.fn(),
      onRequestCancel: vi.fn(),
      cancelPending: false,
      mainView: "pipeline" as const,
      onOpenRecommendations: vi.fn(),
      onOpenPipeline: vi.fn(),
    };
    const { rerender } = render(
      <WorkflowRunDetailHeader
        detail={makeDetail({ status: "running" })}
        {...sharedProps}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Cancel workflow" }),
    ).toBeInTheDocument();

    rerender(
      <WorkflowRunDetailHeader
        detail={makeDetail({ status: "completed" })}
        {...sharedProps}
      />,
    );
    expect(
      screen.queryByRole("button", { name: "Cancel workflow" }),
    ).not.toBeInTheDocument();

    rerender(
      <WorkflowRunDetailHeader
        detail={makeDetail({ status: "failed" })}
        {...sharedProps}
      />,
    );
    expect(
      screen.queryByRole("button", { name: "Cancel workflow" }),
    ).not.toBeInTheDocument();

    rerender(
      <WorkflowRunDetailHeader
        detail={makeDetail({ status: "cancelled" })}
        {...sharedProps}
      />,
    );
    expect(
      screen.queryByRole("button", { name: "Cancel workflow" }),
    ).not.toBeInTheDocument();
  });

  it("fires onRequestCancel when clicked", async () => {
    const user = userEvent.setup();
    const onRequestCancel = vi.fn();
    render(
      <WorkflowRunDetailHeader
        detail={makeDetail({ status: "running" })}
        onRequestDelete={vi.fn()}
        onRequestCancel={onRequestCancel}
        cancelPending={false}
        mainView="pipeline"
        onOpenRecommendations={vi.fn()}
        onOpenPipeline={vi.fn()}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Cancel workflow" }));
    expect(onRequestCancel).toHaveBeenCalledTimes(1);
  });

  it("disables cancel button while cancellation is in-flight", () => {
    render(
      <WorkflowRunDetailHeader
        detail={makeDetail({ status: "running" })}
        onRequestDelete={vi.fn()}
        onRequestCancel={vi.fn()}
        cancelPending={true}
        mainView="pipeline"
        onOpenRecommendations={vi.fn()}
        onOpenPipeline={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Cancelling..." }),
    ).toBeDisabled();
  });
});
