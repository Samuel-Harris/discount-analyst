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
  /** Top target handle on the first lane node (unused; edges use left target). */
  handleTargetTop: boolean;
  /** Set on `workflow_surveyor` when multiple stocks each get their own lane. */
  surveyorHubLayout?: boolean;
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
/** Approximate node body height for vertical centring of multi-lane Surveyor. */
const NODE_H = 52;
const TOP_Y = 24;
const LANE_GAP = 112;
const LEFT_MARGIN = 32;

function laneY(laneIndex: number): number {
  return TOP_Y + 88 + laneIndex * LANE_GAP;
}

function columnX(colIndex: number): number {
  return LEFT_MARGIN + colIndex * COL;
}

/** Surveyor-discovered lanes first, then portfolio profiler lanes — keeps hub fan-out readable. */
function runLayoutSort(
  a: WorkflowRunDetailResponse["runs"][0],
  b: WorkflowRunDetailResponse["runs"][0],
): number {
  const rank = (e: EntryPathApi) => (e === "surveyor" ? 0 : 1);
  const dr = rank(a.entry_path) - rank(b.entry_path);
  if (dr !== 0) return dr;
  return a.ticker.localeCompare(b.ticker);
}

/** Display label for pipeline nodes (API slugs stay lowercase on `agentName`). */
function agentDisplayLabel(slug: string): string {
  return slug.toUpperCase();
}

/** Minimum column index of the first agent in each surveyor-entry run (for Surveyor X). */
function minFirstColumnAmongSurveyorRuns(
  runs: WorkflowRunDetailResponse["runs"],
): number | null {
  let minCol: number | null = null;
  for (const run of runs) {
    if (run.entry_path !== "surveyor") continue;
    const sorted = sortAgents(run.agent_executions);
    const first = sorted[0];
    if (!first) continue;
    const idx = CANONICAL_ORDER.indexOf(first.agent_name);
    const col = idx >= 0 ? idx : 0;
    minCol = minCol === null ? col : Math.min(minCol, col);
  }
  return minCol;
}

/** Min/max lane row index among surveyor-entry runs (so the hub centres on every discovery lane). */
function surveyorLaneIndexExtent(
  runs: WorkflowRunDetailResponse["runs"],
): { minLane: number; maxLane: number } | null {
  let minLane: number | null = null;
  let maxLane: number | null = null;
  runs.forEach((run, laneIndex) => {
    if (run.entry_path !== "surveyor") return;
    minLane = minLane === null ? laneIndex : Math.min(minLane, laneIndex);
    maxLane = maxLane === null ? laneIndex : Math.max(maxLane, laneIndex);
  });
  if (minLane === null || maxLane === null) return null;
  return { minLane, maxLane };
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

  const runs = [...detail.runs].sort(runLayoutSort);

  const surveyorEntryRuns = runs.filter((r) => r.entry_path === "surveyor");

  /** Several surveyor-discovered stocks → one horizontal lane each, fanning from Surveyor. */
  const surveyorHubLayout =
    Boolean(detail.surveyor_execution) && surveyorEntryRuns.length > 1;

  /** Row / column for inline Surveyor (single stock) aligned with that lane. */
  let surveyorLaneIndex: number | null = null;
  let surveyorFirstCol: number | null = null;
  if (detail.surveyor_execution && !surveyorHubLayout) {
    runs.forEach((run, laneIndex) => {
      if (run.entry_path !== "surveyor" || surveyorFirstCol !== null) return;
      const sorted = sortAgents(run.agent_executions);
      const first = sorted[0];
      if (!first) return;
      surveyorLaneIndex = laneIndex;
      const idx = CANONICAL_ORDER.indexOf(first.agent_name);
      surveyorFirstCol = idx >= 0 ? idx : 0;
    });
  }

  const surveyorOnLane =
    detail.surveyor_execution &&
    !surveyorHubLayout &&
    surveyorLaneIndex !== null &&
    surveyorFirstCol !== null;

  const surveyorXCentred =
    LEFT_MARGIN +
    Math.max(0, (CANONICAL_ORDER.length * COL - NODE_W) / 2) -
    COL / 2 +
    COL / 2;

  const minSurveyorTargetCol = minFirstColumnAmongSurveyorRuns(runs);

  let surveyorX: number;
  let surveyorY: number;
  if (
    detail.surveyor_execution &&
    surveyorHubLayout &&
    minSurveyorTargetCol !== null
  ) {
    surveyorX = Math.max(4, columnX(minSurveyorTargetCol) - NODE_W - 24);
    const laneExtent = surveyorLaneIndexExtent(runs);
    surveyorY = laneExtent
      ? (laneY(laneExtent.minLane) + laneY(laneExtent.maxLane)) / 2 - NODE_H / 2
      : TOP_Y;
  } else if (surveyorOnLane) {
    surveyorX = Math.max(4, columnX(surveyorFirstCol!) - NODE_W - 24);
    surveyorY = laneY(surveyorLaneIndex!);
  } else {
    surveyorX = surveyorXCentred;
    surveyorY = TOP_Y;
  }

  if (detail.surveyor_execution) {
    nodes.push({
      id: surveyorNodeId,
      kind: "workflow_surveyor",
      label: agentDisplayLabel("surveyor"),
      agentName: "surveyor",
      status: detail.surveyor_execution.status,
      runId: null,
      ticker: null,
      entryPath: null,
      workflowRunId: detail.id,
      position: { x: surveyorX, y: surveyorY },
      handleTargetLeft: false,
      handleTargetTop: false,
      surveyorHubLayout,
    });
  }

  runs.forEach((run, laneIndex) => {
    const sorted = sortAgents(run.agent_executions);
    let prevId: string | null = null;

    for (const exec of sorted) {
      const id = `run-${run.id}--${exec.agent_name}`;
      const colIndex = CANONICAL_ORDER.indexOf(exec.agent_name);
      const col = colIndex >= 0 ? colIndex : 0;

      const surveyorIncoming =
        prevId === null &&
        run.entry_path === "surveyor" &&
        Boolean(detail.surveyor_execution);

      const handleTargetTop = false;
      const handleTargetLeft = prevId !== null || surveyorIncoming;

      nodes.push({
        id,
        kind: "lane_agent",
        label: agentDisplayLabel(exec.agent_name),
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
          sourceHandle: "r",
          targetHandle: "l",
        });
      }
      prevId = id;
    }
  });

  return { nodes, edges, surveyorNodeId };
}
