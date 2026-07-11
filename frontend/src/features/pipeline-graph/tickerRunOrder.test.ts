import { describe, expect, it } from "vitest";

import { sortedWorkflowRuns } from "./tickerRunOrder";

describe("sortedWorkflowRuns", () => {
  it("orders surveyor lanes before profiler lanes, then by ticker", () => {
    const runs = [
      {
        id: "p",
        ticker: "META",
        company_name: "M",
        entry_path: "profiler" as const,
        status: "running" as const,
        final_rating: null,
        decision_type: null,
        agent_executions: [],
      },
      {
        id: "s",
        ticker: "DISC.L",
        company_name: "D",
        entry_path: "surveyor" as const,
        status: "running" as const,
        final_rating: null,
        decision_type: null,
        agent_executions: [],
      },
    ];
    expect(sortedWorkflowRuns(runs).map((r) => r.ticker)).toEqual([
      "DISC.L",
      "META",
    ]);
  });
});
