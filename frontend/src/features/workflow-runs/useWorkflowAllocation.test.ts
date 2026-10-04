import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { PortfolioAllocation } from "@/api";
import * as api from "@/api";
import {
  invalidateWorkflowRunDetail,
  resetQueryInvalidationRegistryForTests,
} from "@/lib/server-state/invalidation";
import { useWorkflowAllocation } from "./useWorkflowAllocation";

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

describe("useWorkflowAllocation", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
    resetQueryInvalidationRegistryForTests();
  });

  it("does not fetch when curator status is not completed", async () => {
    const fetch = vi.spyOn(api, "fetchWorkflowAllocation");
    const { result } = renderHook(() =>
      useWorkflowAllocation("wf-1", "running", 60_000),
    );
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(fetch).not.toHaveBeenCalled();
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("does not fetch when curator execution is null", async () => {
    const fetch = vi.spyOn(api, "fetchWorkflowAllocation");
    renderHook(() => useWorkflowAllocation("wf-1", null, 60_000));
    await waitFor(() => {
      expect(fetch).not.toHaveBeenCalled();
    });
  });

  it("fetches allocation once curator has completed", async () => {
    const allocation = sampleAllocation();
    vi.spyOn(api, "fetchWorkflowAllocation").mockResolvedValue(allocation);
    const { result } = renderHook(() =>
      useWorkflowAllocation("wf-1", "completed", 60_000),
    );
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toEqual(allocation);
    expect(result.current.error).toBeNull();
  });

  it("maps 404 to data null without an error", async () => {
    vi.spyOn(api, "fetchWorkflowAllocation").mockResolvedValue(null);
    const { result } = renderHook(() =>
      useWorkflowAllocation("wf-1", "completed", 60_000),
    );
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("surfaces a 500 as an error string", async () => {
    vi.spyOn(api, "fetchWorkflowAllocation").mockRejectedValue(
      new Error("server exploded"),
    );
    const { result } = renderHook(() =>
      useWorkflowAllocation("wf-1", "completed", 60_000),
    );
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe("server exploded");
  });

  it("refetches when the workflow run detail query is invalidated", async () => {
    const fetch = vi
      .spyOn(api, "fetchWorkflowAllocation")
      .mockResolvedValue(sampleAllocation());
    const { unmount } = renderHook(() =>
      useWorkflowAllocation("wf-inv", "completed", 60_000),
    );
    await waitFor(() => expect(fetch).toHaveBeenCalled());
    const base = fetch.mock.calls.length;
    await act(async () => {
      await invalidateWorkflowRunDetail("wf-inv");
    });
    expect(fetch.mock.calls.length).toBe(base + 1);
    unmount();
  });
});
