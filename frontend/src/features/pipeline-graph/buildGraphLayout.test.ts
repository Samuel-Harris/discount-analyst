import { describe, expect, it } from "vitest";

import { PROFILER_ENTRY_AGENT_NAMES } from "./agentLaneOrder";
import { buildGraphLayout } from "./buildGraphLayout";
import type { AgentExecutionSummary, WorkflowRunDetailResponse } from "@/api";

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
    can_retry_failed_agents: false,
    surveyor_execution: {
      id: "wfe-1",
      agent_name: "surveyor",
      status: "completed",
      started_at: "2026-04-01T12:00:01Z",
      completed_at: "2026-04-01T12:00:10Z",
      model_name: "gpt-5.1",
    },
    curator_execution: null,
    runs: [],
    ...overrides,
  };
}

function curatorExecution(
  status: AgentExecutionSummary["status"] = "completed",
): AgentExecutionSummary {
  return {
    id: "wfe-curator",
    agent_name: "curator",
    status,
    started_at: "2026-04-01T12:01:00Z",
    completed_at: status === "completed" ? "2026-04-01T12:01:10Z" : null,
    model_name: "gpt-5.1",
  };
}

describe("buildGraphLayout", () => {
  it("adds a workflow-level Surveyor node when surveyor_execution is present", () => {
    const { nodes, surveyorNodeId } = buildGraphLayout(baseDetail());
    const wf = nodes.find((n) => n.id === surveyorNodeId);
    expect(wf?.kind).toBe("workflow_surveyor");
    expect(wf?.agentName).toBe("surveyor");
    expect(wf?.label).toBe("SURVEYOR");
    expect(wf?.modelName).toBe("gpt-5.1");
  });

  it("passes lane agent model_name through to layout nodes", () => {
    const detail = baseDetail({
      surveyor_execution: null,
      runs: [
        {
          id: "run-p",
          ticker: "ORD.L",
          company_name: "ORD",
          entry_path: "profiler",
          status: "running",
          final_rating: null,
          decision_type: null,
          agent_executions: [
            {
              id: "a-prof",
              agent_name: "profiler",
              status: "running",
              started_at: null,
              completed_at: null,
              model_name: "claude-opus-4-6",
            },
          ],
        },
      ],
    });
    const { nodes } = buildGraphLayout(detail);
    const profiler = nodes.find(
      (n) => n.kind === "lane_agent" && n.agentName === "profiler",
    );
    expect(profiler?.modelName).toBe("claude-opus-4-6");
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
    const fromSurveyor = edges.find(
      (e) => e.source === surveyorNodeId && e.targetHandle === "l",
    );
    expect(fromSurveyor).toBeDefined();
    expect(fromSurveyor?.sourceHandle).toBe("r");
  });

  it("sorts profiler lane agents into backend contract column order", () => {
    const detail = baseDetail({
      runs: [
        {
          id: "run-p",
          ticker: "ORD.L",
          company_name: "ORD",
          entry_path: "profiler",
          status: "running",
          final_rating: null,
          decision_type: null,
          agent_executions: [
            {
              id: "a-app",
              agent_name: "appraiser",
              status: "pending",
              started_at: null,
              completed_at: null,
            },
            {
              id: "a-prof",
              agent_name: "profiler",
              status: "completed",
              started_at: null,
              completed_at: null,
            },
            {
              id: "a-res",
              agent_name: "researcher",
              status: "running",
              started_at: null,
              completed_at: null,
            },
          ],
        },
      ],
    });
    const executions = detail.runs[0]!.agent_executions;
    const present = new Set(executions.map((e) => e.agent_name));
    const expectedLeftToRight = PROFILER_ENTRY_AGENT_NAMES.filter((slug) =>
      present.has(slug),
    );
    const { nodes } = buildGraphLayout(detail);
    const lane = nodes.filter((n) => n.kind === "lane_agent");
    const ordered = [...lane].sort((a, b) => a.position.x - b.position.x);
    expect(ordered.map((n) => n.agentName)).toEqual([...expectedLeftToRight]);
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

  it("uses hub Surveyor with a fan-out edge per stock when several surveyor lanes exist", () => {
    const detail = baseDetail({
      runs: [
        {
          id: "run-disc",
          ticker: "disc.l",
          company_name: "D",
          entry_path: "surveyor",
          status: "completed",
          final_rating: null,
          decision_type: null,
          agent_executions: [
            {
              id: "d1",
              agent_name: "researcher",
              status: "completed",
              started_at: null,
              completed_at: null,
            },
          ],
        },
        {
          id: "run-meta",
          ticker: "meta",
          company_name: "M",
          entry_path: "surveyor",
          status: "completed",
          final_rating: null,
          decision_type: null,
          agent_executions: [
            {
              id: "m1",
              agent_name: "researcher",
              status: "completed",
              started_at: null,
              completed_at: null,
            },
          ],
        },
      ],
    });
    const { nodes, edges, surveyorNodeId } = buildGraphLayout(detail);
    const wf = nodes.find((n) => n.id === surveyorNodeId);
    expect(wf?.surveyorHubLayout).toBe(true);
    const researcherColX = 32 + 150; /* LEFT_MARGIN + 1 * COL */
    expect(wf?.position.x ?? 999).toBeLessThan(researcherColX);
    /* laneY(0)=112, laneY(1)=224, NODE_H=52 */
    expect(wf?.position.y).toBe(142);
    const fan = edges.filter(
      (e) =>
        e.source === surveyorNodeId &&
        e.sourceHandle === "r" &&
        e.targetHandle === "l",
    );
    expect(fan).toHaveLength(2);
  });

  it("places surveyor-discovery lanes before profiler portfolio lanes", () => {
    const detail = baseDetail({
      runs: [
        {
          id: "run-meta",
          ticker: "META",
          company_name: "M",
          entry_path: "profiler",
          status: "running",
          final_rating: null,
          decision_type: null,
          agent_executions: [
            {
              id: "m1",
              agent_name: "profiler",
              status: "pending",
              started_at: null,
              completed_at: null,
            },
          ],
        },
        {
          id: "run-disc",
          ticker: "DISC.L",
          company_name: "D",
          entry_path: "surveyor",
          status: "running",
          final_rating: null,
          decision_type: null,
          agent_executions: [
            {
              id: "d1",
              agent_name: "researcher",
              status: "running",
              started_at: null,
              completed_at: null,
            },
          ],
        },
      ],
    });
    const { nodes } = buildGraphLayout(detail);
    const discY = nodes.find(
      (n) => n.kind === "lane_agent" && n.ticker === "DISC.L",
    )?.position.y;
    const metaY = nodes.find(
      (n) => n.kind === "lane_agent" && n.ticker === "META",
    )?.position.y;
    expect(discY).toBeDefined();
    expect(metaY).toBeDefined();
    expect(discY!).toBeLessThan(metaY!);
  });

  it("lays out multiple ticker lanes with distinct y positions", () => {
    const detail = baseDetail({
      runs: [
        {
          id: "run-1",
          ticker: "AAA.L",
          company_name: "A",
          entry_path: "profiler",
          status: "running",
          final_rating: null,
          decision_type: null,
          agent_executions: [
            {
              id: "a1",
              agent_name: "profiler",
              status: "completed",
              started_at: null,
              completed_at: null,
            },
          ],
        },
        {
          id: "run-2",
          ticker: "ZZZ.L",
          company_name: "Z",
          entry_path: "profiler",
          status: "running",
          final_rating: null,
          decision_type: null,
          agent_executions: [
            {
              id: "z1",
              agent_name: "profiler",
              status: "running",
              started_at: null,
              completed_at: null,
            },
          ],
        },
      ],
    });
    const { nodes } = buildGraphLayout(detail);
    const laneAgents = nodes.filter((n) => n.kind === "lane_agent");
    const yForAaa = laneAgents.find((n) => n.ticker === "AAA.L")?.position.y;
    const yForZzz = laneAgents.find((n) => n.ticker === "ZZZ.L")?.position.y;
    expect(yForAaa).toBeDefined();
    expect(yForZzz).toBeDefined();
    expect(yForAaa).not.toBe(yForZzz);
  });

  it("adds a workflow-level Curator node to the right of the last lane agent", () => {
    const detail = baseDetail({
      curator_execution: curatorExecution(),
      surveyor_execution: null,
      runs: [
        {
          id: "run-p",
          ticker: "ORD.L",
          company_name: "ORD",
          entry_path: "profiler",
          status: "completed",
          final_rating: "HOLD",
          decision_type: "rating_table",
          agent_executions: [
            {
              id: "a-prof",
              agent_name: "profiler",
              status: "completed",
              started_at: null,
              completed_at: null,
            },
            {
              id: "a-res",
              agent_name: "researcher",
              status: "completed",
              started_at: null,
              completed_at: null,
            },
          ],
        },
      ],
    });
    const { nodes, edges, curatorNodeId } = buildGraphLayout(detail);
    const curator = nodes.find((n) => n.id === curatorNodeId);
    expect(curator?.kind).toBe("workflow_curator");
    expect(curator?.label).toBe("CURATOR");
    expect(curator?.status).toBe("completed");
    const researcher = nodes.find(
      (n) => n.kind === "lane_agent" && n.agentName === "researcher",
    );
    expect(curator?.position.x).toBeGreaterThan(researcher?.position.x ?? 0);
    expect(curator?.position.y).toBe(researcher?.position.y);
    expect(
      edges.some(
        (e) =>
          e.source === researcher?.id &&
          e.target === curatorNodeId &&
          e.sourceHandle === "r" &&
          e.targetHandle === "l",
      ),
    ).toBe(true);
  });

  it("fans every ticker lane into Curator when several lanes exist", () => {
    const detail = baseDetail({
      curator_execution: curatorExecution("skipped"),
      runs: [
        {
          id: "run-a",
          ticker: "AAA.L",
          company_name: "A",
          entry_path: "surveyor",
          status: "completed",
          final_rating: null,
          decision_type: null,
          agent_executions: [
            {
              id: "a1",
              agent_name: "researcher",
              status: "completed",
              started_at: null,
              completed_at: null,
            },
            {
              id: "a2",
              agent_name: "appraiser",
              status: "skipped",
              started_at: null,
              completed_at: null,
            },
          ],
        },
        {
          id: "run-b",
          ticker: "BBB.L",
          company_name: "B",
          entry_path: "surveyor",
          status: "completed",
          final_rating: null,
          decision_type: null,
          agent_executions: [
            {
              id: "b1",
              agent_name: "researcher",
              status: "completed",
              started_at: null,
              completed_at: null,
            },
            {
              id: "b2",
              agent_name: "appraiser",
              status: "skipped",
              started_at: null,
              completed_at: null,
            },
          ],
        },
      ],
    });
    const { nodes, edges, curatorNodeId } = buildGraphLayout(detail);
    const curator = nodes.find((n) => n.id === curatorNodeId);
    expect(curator?.status).toBe("skipped");
    /* laneY(0)=112, laneY(1)=224, NODE_H=52 */
    expect(curator?.position.y).toBe(142);
    const fanIn = edges.filter((e) => e.target === curatorNodeId);
    expect(fanIn).toHaveLength(2);
    expect(fanIn.map((e) => e.source).sort()).toEqual([
      "run-run-a--appraiser",
      "run-run-b--appraiser",
    ]);
  });

  it("omits Curator when curator_execution is absent", () => {
    const { nodes } = buildGraphLayout(baseDetail());
    expect(nodes.some((n) => n.kind === "workflow_curator")).toBe(false);
  });
});
