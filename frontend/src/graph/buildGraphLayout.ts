import type {
  AgentExecutionSummary,
  AgentNameSlug,
  EntryPathApi,
  WorkflowRunDetailResponse,
} from "../api";

const CANONICAL_ORDER: AgentNameSlug[] = [
  "profiler",
  "researcher",
  "strategist",
  "sentinel",
  "appraiser",
  "arbiter",
];

function sortAgents(
  executions: AgentExecutionSummary[],
): AgentExecutionSummary[] {
  const rank = new Map(CANONICAL_ORDER.map((a, i) => [a, i]));
  return [...executions].sort(
    (a, b) => (rank.get(a.agent_name) ?? 99) - (rank.get(b.agent_name) ?? 99),
  );
}

export type GraphNodeKind = "workflow_surveyor" | "lane_agent";

export interface LayoutNode {
  id: string;
  kind: GraphNodeKind;
  label: string;
  agentName: AgentNameSlug;
  status: AgentExecutionSummary["status"];
  runId: string | null;
  ticker: string | null;
  entryPath: EntryPathApi | null;
  workflowRunId: string;
  position: { x: number; y: number };
  /** React Flow handles: left target for intra-lane edges */
  handleTargetLeft: boolean;
  /** Top target for workflow Surveyor → first Researcher */
  handleTargetTop: boolean;
}

export interface LayoutEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

const COL = 150;
const NODE_W = 118;
const TOP_Y = 24;
const LANE_GAP = 112;
const LEFT_MARGIN = 32;

function laneY(laneIndex: number): number {
  return TOP_Y + 88 + laneIndex * LANE_GAP;
}

function columnX(colIndex: number): number {
  return LEFT_MARGIN + colIndex * COL;
}

/** Builds positioned nodes and edges for the grouped workflow graph. */
export function buildGraphLayout(detail: WorkflowRunDetailResponse): {
  nodes: LayoutNode[];
  edges: LayoutEdge[];
  surveyorNodeId: string;
} {
  const surveyorNodeId = `wf-${detail.id}-surveyor`;
  const nodes: LayoutNode[] = [];
  const edges: LayoutEdge[] = [];

  const runs = [...detail.runs].sort((a, b) =>
    a.ticker.localeCompare(b.ticker),
  );

  const surveyorX =
    LEFT_MARGIN +
    Math.max(0, (CANONICAL_ORDER.length * COL - NODE_W) / 2) -
    COL / 2 +
    COL / 2;

  if (detail.surveyor_execution) {
    nodes.push({
      id: surveyorNodeId,
      kind: "workflow_surveyor",
      label: "surveyor",
      agentName: "surveyor",
      status: detail.surveyor_execution.status,
      runId: null,
      ticker: null,
      entryPath: null,
      workflowRunId: detail.id,
      position: { x: surveyorX, y: TOP_Y },
      handleTargetLeft: false,
      handleTargetTop: false,
    });
  }

  runs.forEach((run, laneIndex) => {
    const sorted = sortAgents(run.agent_executions);
    let prevId: string | null = null;

    for (const exec of sorted) {
      const id = `run-${run.id}--${exec.agent_name}`;
      const colIndex = CANONICAL_ORDER.indexOf(exec.agent_name);
      const col = colIndex >= 0 ? colIndex : 0;

      const handleTargetLeft = prevId !== null;
      const handleTargetTop =
        prevId === null &&
        run.entry_path === "surveyor" &&
        Boolean(detail.surveyor_execution);

      nodes.push({
        id,
        kind: "lane_agent",
        label: exec.agent_name,
        agentName: exec.agent_name,
        status: exec.status,
        runId: run.id,
        ticker: run.ticker,
        entryPath: run.entry_path,
        workflowRunId: detail.id,
        position: { x: columnX(col), y: laneY(laneIndex) },
        handleTargetLeft,
        handleTargetTop,
      });

      if (prevId) {
        edges.push({
          id: `e-${prevId}-${id}`,
          source: prevId,
          target: id,
          sourceHandle: "r",
          targetHandle: "l",
        });
      } else if (run.entry_path === "surveyor" && detail.surveyor_execution) {
        edges.push({
          id: `e-${surveyorNodeId}-${id}`,
          source: surveyorNodeId,
          target: id,
          sourceHandle: "b",
          targetHandle: "t",
        });
      }
      prevId = id;
    }
  });

  return { nodes, edges, surveyorNodeId };
}
