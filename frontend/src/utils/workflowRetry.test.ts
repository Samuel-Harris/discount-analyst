import { describe, expect, it } from "vitest";

import type {
  AgentExecutionSummary,
  AgentNameSlug,
  ExecutionStatusApi,
  TickerRunDetail,
  WorkflowRunDetailResponse,
} from "../api";
import {
  hasRetriableFailedAgents,
  isGateAbortFailedRun,
} from "./workflowRetry";

function makeExecution(
  overrides: Partial<AgentExecutionSummary> &
    Pick<AgentExecutionSummary, "id" | "agent_name" | "status">,
): AgentExecutionSummary {
  return {
    started_at: null,
    completed_at: null,
    ...overrides,
  };
}

function makeLaneExecutions(
  statuses: Array<[string, AgentNameSlug, ExecutionStatusApi]>,
): AgentExecutionSummary[] {
  return statuses.map(([id, agent_name, status]) =>
    makeExecution({ id, agent_name, status }),
  );
}

function makeRun(overrides: Partial<TickerRunDetail> = {}): TickerRunDetail {
  return {
    id: "run-1",
    ticker: "NATR",
    company_name: "Nature's Sunshine",
    entry_path: "surveyor",
    status: "failed",
    final_rating: null,
    decision_type: null,
    agent_executions: [],
    ...overrides,
  };
}

function makeDetail(
  overrides: Partial<WorkflowRunDetailResponse> = {},
): WorkflowRunDetailResponse {
  return {
    id: "wf-1",
    started_at: "2026-04-01T12:00:00Z",
    completed_at: "2026-04-01T13:00:00Z",
    status: "failed",
    is_mock: false,
    error_message: null,
    surveyor_execution: null,
    runs: [],
    ...overrides,
  };
}

describe("isGateAbortFailedRun", () => {
  it("returns true when a failed run has only skipped lane agents", () => {
    expect(
      isGateAbortFailedRun(
        makeRun({
          agent_executions: makeLaneExecutions([
            ["1", "researcher", "skipped"],
            ["2", "strategist", "skipped"],
            ["3", "sentinel", "skipped"],
            ["4", "appraiser", "skipped"],
          ]),
        }),
      ),
    ).toBe(true);
  });

  it("returns false when a lane agent failed", () => {
    expect(
      isGateAbortFailedRun(
        makeRun({
          agent_executions: makeLaneExecutions([
            ["1", "researcher", "completed"],
            ["2", "strategist", "completed"],
            ["3", "sentinel", "completed"],
            ["4", "appraiser", "failed"],
          ]),
        }),
      ),
    ).toBe(false);
  });

  it("returns false for completed data-quality rejections", () => {
    expect(
      isGateAbortFailedRun(
        makeRun({
          status: "completed",
          decision_type: "data_quality_rejection",
          agent_executions: [
            makeExecution({
              id: "1",
              agent_name: "researcher",
              status: "skipped",
            }),
          ],
        }),
      ),
    ).toBe(false);
  });
});

describe("hasRetriableFailedAgents", () => {
  it("returns true for gate-abort failed runs without failed agent rows", () => {
    expect(
      hasRetriableFailedAgents(
        makeDetail({
          runs: [
            makeRun({
              agent_executions: makeLaneExecutions([
                ["1", "researcher", "skipped"],
                ["2", "strategist", "skipped"],
                ["3", "sentinel", "skipped"],
                ["4", "appraiser", "skipped"],
              ]),
            }),
          ],
        }),
      ),
    ).toBe(true);
  });

  it("returns false when no failed surveyor or lane work exists", () => {
    expect(
      hasRetriableFailedAgents(
        makeDetail({
          status: "completed",
          runs: [
            makeRun({
              status: "completed",
              agent_executions: [
                makeExecution({
                  id: "1",
                  agent_name: "researcher",
                  status: "completed",
                }),
              ],
            }),
          ],
        }),
      ),
    ).toBe(false);
  });
});
