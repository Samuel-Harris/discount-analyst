import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { WorkflowRunDetailResponse, WorkflowRunListItem } from "@/api";
import * as api from "@/api";
import { useConversation } from "@/features/agent-conversation/useConversation";
import { useWorkflowRunDetail } from "@/features/workflow-runs/useWorkflowRunDetail";
import { useWorkflowRunNavigation } from "@/features/workflow-runs/useWorkflowRunNavigation";
import { useWorkflowRuns } from "@/features/workflow-runs/useWorkflowRuns";
import * as serverState from "@/lib/server-state/invalidation";
import { DashboardShell } from "./DashboardShell";
import { useYfinanceFreshness } from "./useYfinanceFreshness";

vi.mock("@/features/workflow-runs/useWorkflowRuns", () => ({
  useWorkflowRuns: vi.fn(),
}));
vi.mock("@/features/workflow-runs/useWorkflowRunNavigation", () => ({
  useWorkflowRunNavigation: vi.fn(),
}));
vi.mock("@/features/workflow-runs/useWorkflowRunDetail", () => ({
  useWorkflowRunDetail: vi.fn(),
}));
vi.mock("@/features/agent-conversation/useConversation", () => ({
  useConversation: vi.fn(),
}));
vi.mock("@/features/workflow-runs/RunPipelineForm", () => ({
  RunPipelineForm: () => <div data-testid="run-pipeline-form" />,
}));
vi.mock("@/features/agent-conversation/AgentPanel", () => ({
  AgentPanel: () => null,
}));
vi.mock("./layout/AppHeader", () => ({ AppHeader: () => null }));
vi.mock("./useYfinanceFreshness", () => ({
  useYfinanceFreshness: vi.fn(() => null),
}));
vi.mock("./WorkflowRunMainPanel", () => ({
  WorkflowRunMainPanel: (props: {
    detail: WorkflowRunDetailResponse | null;
    workflowActionError: string | null;
    onRequestCancelRun: (id: string) => void;
  }) => (
    <div>
      {props.detail ? (
        <button
          type="button"
          onClick={() => {
            if (!props.detail) return;
            props.onRequestCancelRun(props.detail.id);
          }}
        >
          Cancel workflow
        </button>
      ) : null}
      {props.workflowActionError ? (
        <div>{props.workflowActionError}</div>
      ) : null}
    </div>
  ),
}));

function makeListItem(): WorkflowRunListItem {
  return {
    id: "wf-1",
    started_at: "2026-04-01T12:00:00Z",
    completed_at: null,
    status: "running",
    is_mock: false,
    error_message: null,
    ticker_run_count: 1,
    completed_ticker_run_count: 0,
    failed_ticker_run_count: 0,
  };
}

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
    surveyor_execution: {
      id: "wfe-1",
      agent_name: "surveyor",
      status: "running",
      started_at: null,
      completed_at: null,
    },
    allocator_execution: null,
    runs: [],
    ...overrides,
  };
}

describe("DashboardShell cancellation", () => {
  beforeEach(() => {
    vi.mocked(useWorkflowRuns).mockReturnValue({
      items: [makeListItem()],
      loading: false,
      error: null,
      refresh: vi.fn(),
    });
    vi.mocked(useWorkflowRunNavigation).mockReturnValue({
      selectedId: "wf-1",
      mainView: "pipeline",
      selectRunFromSidebar: vi.fn(),
      openLaunchedRun: vi.fn(),
      openRecommendations: vi.fn(),
      openPipeline: vi.fn(),
    });
    vi.mocked(useWorkflowRunDetail).mockReturnValue({
      detail: makeDetail(),
      loading: false,
      error: null,
      refresh: vi.fn(),
    });
    vi.mocked(useConversation).mockReturnValue({
      data: null,
      loading: false,
      error: null,
      load: vi.fn(),
      clear: vi.fn(),
    });
    vi.mocked(useYfinanceFreshness).mockReturnValue(null);
    vi.spyOn(window, "confirm").mockReturnValue(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("calls cancel API and invalidates list + detail polling", async () => {
    const user = userEvent.setup();
    const cancelSpy = vi.spyOn(api, "cancelWorkflowRun").mockResolvedValue();
    const invalidateListSpy = vi
      .spyOn(serverState, "invalidateWorkflowRunsList")
      .mockResolvedValue();
    const invalidateDetailSpy = vi
      .spyOn(serverState, "invalidateWorkflowRunDetail")
      .mockResolvedValue();

    render(<DashboardShell />);
    await user.click(screen.getByRole("button", { name: "Cancel workflow" }));

    await waitFor(() => {
      expect(cancelSpy).toHaveBeenCalledWith("wf-1");
    });
    expect(invalidateListSpy).toHaveBeenCalledTimes(1);
    expect(invalidateDetailSpy).toHaveBeenCalledWith("wf-1");
  });

  it("shows action errors when cancel fails", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "cancelWorkflowRun").mockRejectedValue(
      new Error("Cancel failed badly"),
    );
    vi.spyOn(serverState, "invalidateWorkflowRunsList").mockResolvedValue();
    vi.spyOn(serverState, "invalidateWorkflowRunDetail").mockResolvedValue();

    render(<DashboardShell />);
    await user.click(screen.getByRole("button", { name: "Cancel workflow" }));

    expect(await screen.findByText("Cancel failed badly")).toBeInTheDocument();
  });

  it("shows a yfinance banner when the installed package is behind PyPI", () => {
    vi.mocked(useYfinanceFreshness).mockReturnValue({
      installed_version: "1.6.0",
      latest_version: "1.7.0",
      is_outdated: true,
    });
    render(<DashboardShell />);
    expect(screen.getByRole("status")).toHaveTextContent(
      "yfinance 1.6.0 is installed; 1.7.0 is available on PyPI",
    );
  });
});
