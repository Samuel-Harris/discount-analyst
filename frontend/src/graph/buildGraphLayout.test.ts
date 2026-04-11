import { describe, expect, it } from "vitest";

import { buildGraphLayout } from "./buildGraphLayout";
import type { WorkflowRunDetailResponse } from "../api";

function baseDetail(
  overrides: Partial<WorkflowRunDetailResponse> = {},
): WorkflowRunDetailResponse {
  return {
    id: "wf-1",
    started_at: "2026-04-01T12:00:00Z",
    completed_at: null,
    status: "running",
    is_mock: true,
    error_message: null,
    surveyor_execution: {
      id: "wfe-1",
      agent_name: "surveyor",
      status: "completed",
      started_at: "2026-04-01T12:00:01Z",
      completed_at: "2026-04-01T12:00:10Z",
    },
    runs: [],
    ...overrides,
  };
}

describe("buildGraphLayout", () => {
  it("adds a workflow-level Surveyor node when surveyor_execution is present", () => {
    const { nodes, surveyorNodeId } = buildGraphLayout(baseDetail());
    const wf = nodes.find((n) => n.id === surveyorNodeId);
    expect(wf?.kind).toBe("workflow_surveyor");
    expect(wf?.agentName).toBe("surveyor");
  });

  it("links Surveyor workflow node to the first lane agent for surveyor entry paths", () => {
    const detail = baseDetail({
      runs: [
        {
          id: "run-a",
          ticker: "AAA.L",
          company_name: "AAA",
          entry_path: "surveyor",
          status: "running",
          final_rating: null,
          decision_type: null,
          agent_executions: [
            {
              id: "x1",
              agent_name: "researcher",
              status: "running",
              started_at: null,
              completed_at: null,
            },
          ],
        },
      ],
    });
    const { edges, surveyorNodeId } = buildGraphLayout(detail);
    const down = edges.find(
      (e) => e.source === surveyorNodeId && e.targetHandle === "t",
    );
    expect(down).toBeDefined();
    expect(down?.sourceHandle).toBe("b");
  });

  it("chains profiler lanes horizontally without Surveyor→lane edge", () => {
    const detail = baseDetail({
      runs: [
        {
          id: "run-p",
          ticker: "BBB.L",
          company_name: "BBB",
          entry_path: "profiler",
          status: "running",
          final_rating: null,
          decision_type: null,
          agent_executions: [
            {
              id: "p1",
              agent_name: "profiler",
              status: "completed",
              started_at: null,
              completed_at: null,
            },
            {
              id: "p2",
              agent_name: "researcher",
              status: "running",
              started_at: null,
              completed_at: null,
            },
          ],
        },
      ],
    });
    const { edges, surveyorNodeId } = buildGraphLayout(detail);
    expect(edges.some((e) => e.source === surveyorNodeId)).toBe(false);
    const chain = edges.find(
      (e) => e.sourceHandle === "r" && e.targetHandle === "l",
    );
    expect(chain).toBeDefined();
  });
});
