import type {
  AllocationPosition,
  ExecutionStatusApi,
  PortfolioAllocation,
  RebalanceAction,
} from "@/api";

export type CuratorBookPane =
  | { kind: "book"; allocation: PortfolioAllocation }
  | { kind: "status"; message: string };

export function curatorBookStatusMessage(
  status: Exclude<ExecutionStatusApi, "completed"> | null,
): string {
  switch (status) {
    case null:
    case "pending":
      return "Curator has not started yet.";
    case "running":
      return "Curator is sizing the portfolio…";
    case "skipped":
      return "Curator skipped.";
    case "rejected":
      return "Curator rejected.";
    case "failed":
      return "Curator failed.";
    case "cancelled":
      return "Curator cancelled.";
    default: {
      const unhandled: never = status;
      return unhandled;
    }
  }
}

export function curatorBookPane(
  curatorStatus: ExecutionStatusApi | null,
  allocation: {
    data: PortfolioAllocation | null;
    loading: boolean;
    error: string | null;
  },
): CuratorBookPane {
  if (allocation.data) {
    return { kind: "book", allocation: allocation.data };
  }
  if (curatorStatus !== "completed") {
    return {
      kind: "status",
      message: curatorBookStatusMessage(curatorStatus),
    };
  }
  if (allocation.loading) {
    return { kind: "status", message: "Loading allocation…" };
  }
  if (allocation.error) {
    return { kind: "status", message: "Could not load allocation." };
  }
  return {
    kind: "status",
    message: "Curator completed, allocation not available yet.",
  };
}

export function formatWeightPct(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function formatWeightChange(current: number, target: number): string {
  return `${formatWeightPct(current)} → ${formatWeightPct(target)}`;
}

export function formatWeightBand(low: number, high: number): string {
  return `${low.toFixed(1)}–${high.toFixed(1)}%`;
}

export function formatRebalanceAction(action: RebalanceAction): string {
  switch (action) {
    case "enter":
      return "Enter";
    case "increase":
      return "Increase";
    case "hold":
      return "Hold";
    case "reduce":
      return "Reduce";
    case "exit":
      return "Exit";
    case "avoid":
      return "Avoid";
    default: {
      const unhandled: never = action;
      void unhandled;
      return "Unknown";
    }
  }
}

export function formatBookMembership(
  isExisting: boolean,
): "Holding" | "New" {
  return isExisting ? "Holding" : "New";
}

/** Current holdings and names with a positive target weight; omit unheld Avoid rows. */
export function isDisplayedBookPosition(position: AllocationPosition): boolean {
  return position.is_existing_position || position.target_weight_pct > 0;
}
