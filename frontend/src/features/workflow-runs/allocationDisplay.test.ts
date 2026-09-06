import { describe, expect, it } from "vitest";

import type {
  AllocationPosition,
  ExecutionStatusApi,
  PortfolioAllocation,
  RebalanceAction,
} from "@/api";
import {
  curatorBookPane,
  curatorBookStatusMessage,
  formatBookMembership,
  formatRebalanceAction,
  formatWeightBand,
  formatWeightChange,
  formatWeightPct,
  isDisplayedBookPosition,
} from "./allocationDisplay";

const nonCompletedStatuses: Exclude<ExecutionStatusApi, "completed">[] = [
  "pending",
  "running",
  "skipped",
  "rejected",
  "failed",
  "cancelled",
];

const rebalanceActions: RebalanceAction[] = [
  "enter",
  "increase",
  "hold",
  "reduce",
  "exit",
  "avoid",
];

function emptyQuery(overrides: {
  data?: PortfolioAllocation | null;
  loading?: boolean;
  error?: string | null;
} = {}) {
  return {
    data: null,
    loading: false,
    error: null,
    ...overrides,
  };
}

describe("curatorBookStatusMessage", () => {
  it("covers every non-completed execution status and null", () => {
    const expected: Record<Exclude<ExecutionStatusApi, "completed">, string> = {
      pending: "Curator has not started yet.",
      running: "Curator is sizing the portfolio…",
      skipped: "Curator skipped.",
      rejected: "Curator rejected.",
      failed: "Curator failed.",
      cancelled: "Curator cancelled.",
    };

    expect(curatorBookStatusMessage(null)).toBe("Curator has not started yet.");
    for (const status of nonCompletedStatuses) {
      expect(curatorBookStatusMessage(status)).toBe(expected[status]);
    }
  });
});

describe("curatorBookPane", () => {
  const allocation: PortfolioAllocation = {
    allocation_date: "2026-09-06",
    portfolio_rationale: "Seed book.",
    cash: {
      current_weight_pct: 20,
      target_weight_pct: 85,
      acceptable_weight_low_pct: 84,
      acceptable_weight_high_pct: 86,
      rationale: "Cash.",
    },
    positions: [],
    shared_risk_clusters: [],
  };

  it("returns the book when allocation data is present", () => {
    expect(
      curatorBookPane("completed", emptyQuery({ data: allocation })),
    ).toEqual({ kind: "book", allocation });
  });

  it("returns status copy when Curator has not completed", () => {
    expect(curatorBookPane(null, emptyQuery())).toEqual({
      kind: "status",
      message: "Curator has not started yet.",
    });
    expect(curatorBookPane("running", emptyQuery())).toEqual({
      kind: "status",
      message: "Curator is sizing the portfolio…",
    });
  });

  it("returns completed loading, missing, and error copy", () => {
    expect(
      curatorBookPane("completed", emptyQuery({ loading: true })),
    ).toEqual({
      kind: "status",
      message: "Loading allocation…",
    });
    expect(curatorBookPane("completed", emptyQuery())).toEqual({
      kind: "status",
      message: "Curator completed, allocation not available yet.",
    });
    expect(
      curatorBookPane("completed", emptyQuery({ error: "server exploded" })),
    ).toEqual({
      kind: "status",
      message: "Could not load allocation.",
    });
  });
});

describe("weight formatting", () => {
  it("formats a percentage to one decimal place", () => {
    expect(formatWeightPct(80)).toBe("80.0%");
    expect(formatWeightPct(15)).toBe("15.0%");
    expect(formatWeightPct(0)).toBe("0.0%");
  });

  it("formats current → target weights", () => {
    expect(formatWeightChange(80, 15)).toBe("80.0% → 15.0%");
    expect(formatWeightChange(20, 85)).toBe("20.0% → 85.0%");
  });

  it("formats a low–high band with an en dash", () => {
    expect(formatWeightBand(14, 15)).toBe("14.0–15.0%");
    expect(formatWeightBand(84, 86)).toBe("84.0–86.0%");
  });
});

describe("formatRebalanceAction", () => {
  it("labels every rebalance action", () => {
    const expected: Record<RebalanceAction, string> = {
      enter: "Enter",
      increase: "Increase",
      hold: "Hold",
      reduce: "Reduce",
      exit: "Exit",
      avoid: "Avoid",
    };
    for (const action of rebalanceActions) {
      expect(formatRebalanceAction(action)).toBe(expected[action]);
    }
  });
});

describe("formatBookMembership", () => {
  it("maps existing positions to Holding and new names to New", () => {
    expect(formatBookMembership(true)).toBe("Holding");
    expect(formatBookMembership(false)).toBe("New");
  });
});

function bookPosition(
  overrides: Partial<AllocationPosition> & Pick<AllocationPosition, "ticker">,
): AllocationPosition {
  return {
    company_name: overrides.ticker,
    source_run_id: `run-${overrides.ticker}`,
    is_existing_position: false,
    current_weight_pct: 0,
    target_weight_pct: 0,
    acceptable_weight_low_pct: 0,
    acceptable_weight_high_pct: 0,
    action: "avoid",
    rationale: "rationale",
    policy: { kind: "investable" },
    ...overrides,
  };
}

describe("isDisplayedBookPosition", () => {
  it("keeps current holdings, including exits to zero", () => {
    expect(
      isDisplayedBookPosition(
        bookPosition({
          ticker: "HOLD.L",
          is_existing_position: true,
          current_weight_pct: 80,
          target_weight_pct: 15,
          action: "reduce",
        }),
      ),
    ).toBe(true);
    expect(
      isDisplayedBookPosition(
        bookPosition({
          ticker: "EXIT.L",
          is_existing_position: true,
          current_weight_pct: 10,
          target_weight_pct: 0,
          action: "exit",
        }),
      ),
    ).toBe(true);
  });

  it("keeps new names with a positive target weight", () => {
    expect(
      isDisplayedBookPosition(
        bookPosition({
          ticker: "NEW.L",
          is_existing_position: false,
          target_weight_pct: 8,
          action: "enter",
        }),
      ),
    ).toBe(true);
  });

  it("omits unheld Avoid names", () => {
    expect(
      isDisplayedBookPosition(
        bookPosition({
          ticker: "SKIP.L",
          is_existing_position: false,
          target_weight_pct: 0,
          action: "avoid",
        }),
      ),
    ).toBe(false);
  });
});
