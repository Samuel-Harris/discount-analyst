import { afterEach, describe, expect, it, vi } from "vitest";

import { DashboardApiError } from "./orval-mutator";
import { fetchWorkflowAllocation } from "./index";
import * as generated from "./generated";
import type { PortfolioAllocation } from "./generated";

function sampleAllocation(): PortfolioAllocation {
  return {
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
}

describe("fetchWorkflowAllocation", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns the allocation payload", async () => {
    const allocation = sampleAllocation();
    vi.spyOn(
      generated,
      "getWorkflowAllocationApiWorkflowRunsWorkflowRunIdAllocationGet",
    ).mockResolvedValue(allocation);

    await expect(fetchWorkflowAllocation("wf-1")).resolves.toEqual(allocation);
  });

  it("maps HTTP 404 to null", async () => {
    vi.spyOn(
      generated,
      "getWorkflowAllocationApiWorkflowRunsWorkflowRunIdAllocationGet",
    ).mockRejectedValue(new DashboardApiError("Allocation not found", 404, ""));

    await expect(fetchWorkflowAllocation("wf-missing")).resolves.toBeNull();
  });

  it("rethrows non-404 API errors", async () => {
    const err = new DashboardApiError("boom", 500, "boom");
    vi.spyOn(
      generated,
      "getWorkflowAllocationApiWorkflowRunsWorkflowRunIdAllocationGet",
    ).mockRejectedValue(err);

    await expect(fetchWorkflowAllocation("wf-1")).rejects.toBe(err);
  });
});
