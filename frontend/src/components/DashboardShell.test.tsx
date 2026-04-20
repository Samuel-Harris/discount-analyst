import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { WorkflowRunDetailResponse, WorkflowRunListItem } from "../api";
import * as api from "../api";
import * as serverState from "../serverState";
import { useConversation } from "../hooks/useConversation";
import { useWorkflowRunDetail } from "../hooks/useWorkflowRunDetail";
import { useWorkflowRunNavigation } from "../hooks/useWorkflowRunNavigation";
import { useWorkflowRuns } from "../hooks/useWorkflowRuns";
import { DashboardShell } from "./DashboardShell";

vi.mock("../hooks/useWorkflowRuns", () => ({ useWorkflowRuns: vi.fn() }));
vi.mock("../hooks/useWorkflowRunNavigation", () => ({
  useWorkflowRunNavigation: vi.fn(),
}));
vi.mock("../hooks/useWorkflowRunDetail", () => ({
  useWorkflowRunDetail: vi.fn(),
}));
vi.mock("../hooks/useConversation", () => ({ useConversation: vi.fn() }));
vi.mock("./RunPipelineForm", () => ({
  RunPipelineForm: () => <div data-testid="run-pipeline-form" />,
}));
vi.mock("./AgentPanel", () => ({ AgentPanel: () => null }));
vi.mock("./layout/AppHeader", () => ({ AppHeader: () => null }));
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
    surveyor_execution: {
      id: "wfe-1",
      agent_name: "surveyor",
      status: "running",
      started_at: null,
      completed_at: null,
    },
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
});
