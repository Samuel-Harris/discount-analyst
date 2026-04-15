/** Stable keys for shared server queries and invalidation. */

export const WORKFLOW_RUNS_LIST_KEY = "workflowRuns:list";

export function workflowRunDetailKey(workflowRunId: string): string {
  return `workflowRuns:detail:${workflowRunId}`;
}
