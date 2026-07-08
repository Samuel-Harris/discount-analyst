import type { TickerRunDetail, WorkflowRunDetailResponse } from "../api";
import { PROFILER_ENTRY_AGENT_NAMES } from "../graph/agentLaneOrder";

const LANE_AGENT_NAMES = new Set<string>(PROFILER_ENTRY_AGENT_NAMES);

function laneExecutions(run: TickerRunDetail) {
  return run.agent_executions.filter((execution) =>
    LANE_AGENT_NAMES.has(execution.agent_name),
  );
}

/** Gate threw before any lane agent ran: run failed, all lane agents skipped. */
export function isGateAbortFailedRun(run: TickerRunDetail): boolean {
  if (run.status !== "failed") {
    return false;
  }

  const laneAgentExecutions = laneExecutions(run);
  if (laneAgentExecutions.length === 0) {
    return false;
  }

  if (
    laneAgentExecutions.some(
      (execution) =>
        execution.status === "failed" || execution.status === "completed",
    )
  ) {
    return false;
  }

  return laneAgentExecutions.every(
    (execution) => execution.status === "skipped",
  );
}

export function hasRetriableFailedAgents(
  detail: WorkflowRunDetailResponse,
): boolean {
  if (detail.surveyor_execution?.status === "failed") {
    return true;
  }

  return detail.runs.some(
    (run) =>
      run.agent_executions.some((execution) => execution.status === "failed") ||
      isGateAbortFailedRun(run),
  );
}
