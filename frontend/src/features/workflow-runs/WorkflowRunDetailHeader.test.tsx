import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { WorkflowRunDetailResponse } from "@/api";
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
    can_retry_failed_agents: false,
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
      onRequestRetryFailedAgents: vi.fn(),
      cancelPending: false,
      retryFailedAgentsPending: false,
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
        onRequestRetryFailedAgents={vi.fn()}
        cancelPending={false}
        retryFailedAgentsPending={false}
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
        onRequestRetryFailedAgents={vi.fn()}
        cancelPending={true}
        retryFailedAgentsPending={false}
        mainView="pipeline"
        onOpenRecommendations={vi.fn()}
        onOpenPipeline={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Cancelling..." }),
    ).toBeDisabled();
  });

  it("shows retry button for terminal workflows with failed agents", async () => {
    const user = userEvent.setup();
    const onRequestRetryFailedAgents = vi.fn();
    render(
      <WorkflowRunDetailHeader
        detail={makeDetail({
          status: "completed",
          can_retry_failed_agents: true,
          runs: [
            {
              id: "run-1",
              ticker: "ABC.L",
              company_name: "ABC plc",
              entry_path: "profiler",
              status: "failed",
              final_rating: null,
              decision_type: null,
              agent_executions: [
                {
                  id: "exec-1",
                  agent_name: "researcher",
                  status: "failed",
                  started_at: null,
                  completed_at: null,
                },
              ],
            },
          ],
        })}
        onRequestDelete={vi.fn()}
        onRequestCancel={vi.fn()}
        onRequestRetryFailedAgents={onRequestRetryFailedAgents}
        cancelPending={false}
        retryFailedAgentsPending={false}
        mainView="pipeline"
        onOpenRecommendations={vi.fn()}
        onOpenPipeline={vi.fn()}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Retry all failed agents" }),
    );

    expect(onRequestRetryFailedAgents).toHaveBeenCalledTimes(1);
  });

  it("hides retry button without failed agent executions", () => {
    render(
      <WorkflowRunDetailHeader
        detail={makeDetail({ status: "completed" })}
        onRequestDelete={vi.fn()}
        onRequestCancel={vi.fn()}
        onRequestRetryFailedAgents={vi.fn()}
        cancelPending={false}
        retryFailedAgentsPending={false}
        mainView="pipeline"
        onOpenRecommendations={vi.fn()}
        onOpenPipeline={vi.fn()}
      />,
    );

    expect(
      screen.queryByRole("button", { name: "Retry all failed agents" }),
    ).not.toBeInTheDocument();
  });

  it("shows retry button for gate-abort failed runs with only skipped lane agents", () => {
    render(
      <WorkflowRunDetailHeader
        detail={makeDetail({
          status: "failed",
          can_retry_failed_agents: true,
          runs: [
            {
              id: "run-1",
              ticker: "NATR",
              company_name: "Nature's Sunshine",
              entry_path: "surveyor",
              status: "failed",
              final_rating: null,
              decision_type: null,
              agent_executions: [
                {
                  id: "exec-1",
                  agent_name: "researcher",
                  status: "skipped",
                  started_at: null,
                  completed_at: null,
                },
                {
                  id: "exec-2",
                  agent_name: "strategist",
                  status: "skipped",
                  started_at: null,
                  completed_at: null,
                },
                {
                  id: "exec-3",
                  agent_name: "sentinel",
                  status: "skipped",
                  started_at: null,
                  completed_at: null,
                },
                {
                  id: "exec-4",
                  agent_name: "appraiser",
                  status: "skipped",
                  started_at: null,
                  completed_at: null,
                },
              ],
            },
          ],
        })}
        onRequestDelete={vi.fn()}
        onRequestCancel={vi.fn()}
        onRequestRetryFailedAgents={vi.fn()}
        cancelPending={false}
        retryFailedAgentsPending={false}
        mainView="pipeline"
        onOpenRecommendations={vi.fn()}
        onOpenPipeline={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Retry all failed agents" }),
    ).toBeInTheDocument();
  });

  it("disables retry button while retry is in-flight", () => {
    render(
      <WorkflowRunDetailHeader
        detail={makeDetail({
          status: "failed",
          can_retry_failed_agents: true,
          surveyor_execution: {
            id: "surveyor-1",
            agent_name: "surveyor",
            status: "failed",
            started_at: null,
            completed_at: null,
          },
        })}
        onRequestDelete={vi.fn()}
        onRequestCancel={vi.fn()}
        onRequestRetryFailedAgents={vi.fn()}
        cancelPending={false}
        retryFailedAgentsPending={true}
        mainView="pipeline"
        onOpenRecommendations={vi.fn()}
        onOpenPipeline={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Retrying failed agents..." }),
    ).toBeDisabled();
  });
});
