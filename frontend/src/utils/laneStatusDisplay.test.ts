import { describe, expect, it } from "vitest";

import type { TickerRunDetail } from "../api";
import { laneStatusDisplay } from "./laneStatusDisplay";

function run(overrides: Partial<TickerRunDetail>): TickerRunDetail {
  return {
    id: "r1",
    ticker: "TST.L",
    company_name: "T",
    entry_path: "surveyor",
    status: "running",
    final_rating: null,
    decision_type: null,
    agent_executions: [],
    ...overrides,
  };
}

describe("laneStatusDisplay", () => {
  it("returns COMPLETED for a completed lane", () => {
    expect(laneStatusDisplay(run({ status: "completed" }))).toEqual({
      label: "COMPLETED",
      tone: "completed",
      title: undefined,
    });
  });

  it("returns COMPLETED with failed tone when the ticker run failed", () => {
    expect(laneStatusDisplay(run({ status: "failed" }))).toEqual({
      label: "COMPLETED",
      tone: "failed",
      title: "Lane ended with an error",
    });
  });

  it("returns PENDING when the lane is running but every agent is still pending", () => {
    expect(
      laneStatusDisplay(
        run({
          status: "running",
          agent_executions: [
            {
              id: "e1",
              agent_name: "researcher",
              status: "pending",
              started_at: null,
              completed_at: null,
            },
          ],
        }),
      ),
    ).toEqual({
      label: "PENDING",
      tone: "pending",
      title: undefined,
    });
  });

  it("returns RUNNING when any agent has left the pending state", () => {
    expect(
      laneStatusDisplay(
        run({
          status: "running",
          agent_executions: [
            {
              id: "e1",
              agent_name: "researcher",
              status: "completed",
              started_at: null,
              completed_at: null,
            },
            {
              id: "e2",
              agent_name: "strategist",
              status: "running",
              started_at: null,
              completed_at: null,
            },
          ],
        }),
      ),
    ).toEqual({
      label: "RUNNING",
      tone: "running",
      title: undefined,
    });
  });
});
