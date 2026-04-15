import type { TickerRunDetail } from "../api";

export type LaneStatusDisplayLabel = "COMPLETED" | "RUNNING" | "PENDING";

/** Styling key for the recommendations table (`failed` keeps the label COMPLETED). */
export type LaneStatusDisplayTone =
  | "completed"
  | "running"
  | "pending"
  | "failed";

/**
 * Lane status for the recommendations table: COMPLETED, RUNNING, or PENDING only.
 * API `running` is split using agent executions: all pending → PENDING, else RUNNING.
 * API `failed` still reads as COMPLETED with error colouring; hover `title` explains.
 */
export function laneStatusDisplay(run: TickerRunDetail): {
  label: LaneStatusDisplayLabel;
  tone: LaneStatusDisplayTone;
  title: string | undefined;
} {
  if (run.status === "completed") {
    return { label: "COMPLETED", tone: "completed", title: undefined };
  }
  if (run.status === "failed") {
    return {
      label: "COMPLETED",
      tone: "failed",
      title: "Lane ended with an error",
    };
  }
  const execs = run.agent_executions;
  if (
    execs.length === 0 ||
    execs.every((e) => e.status === "pending")
  ) {
    return {
      label: "PENDING",
      tone: "pending",
      title: undefined,
    };
  }
  return { label: "RUNNING", tone: "running", title: undefined };
}
