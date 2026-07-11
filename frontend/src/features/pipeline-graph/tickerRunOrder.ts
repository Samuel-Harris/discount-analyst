import type { EntryPathApi, WorkflowRunDetailResponse } from "@/api";

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

/** Same order as pipeline graph lanes (for tables and summaries). */
export function sortedWorkflowRuns(
  runs: WorkflowRunDetailResponse["runs"],
): WorkflowRunDetailResponse["runs"] {
  return [...runs].sort(runLayoutSort);
}
