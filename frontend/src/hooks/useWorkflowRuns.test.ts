import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { WorkflowRunListItem } from "../api";
import * as api from "../api";
import {
  invalidateWorkflowRunsList,
  resetQueryInvalidationRegistryForTests,
} from "../serverState";
import { useWorkflowRuns } from "./useWorkflowRuns";

const sampleItem = (id: string): WorkflowRunListItem => ({
  id,
  started_at: "2026-04-01T12:00:00Z",
  completed_at: null,
  status: "running",
  is_mock: true,
  error_message: null,
  ticker_run_count: 1,
  completed_ticker_run_count: 0,
  failed_ticker_run_count: 0,
});

describe("useWorkflowRuns", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
    resetQueryInvalidationRegistryForTests();
  });

  it("loads list workflow runs and exposes items", async () => {
    vi.spyOn(api, "fetchWorkflowRuns").mockResolvedValue([sampleItem("wf-a")]);
    const { result } = renderHook(() => useWorkflowRuns(60_000));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toBeNull();
    expect(result.current.items).toHaveLength(1);
    expect(result.current.items[0].id).toBe("wf-a");
  });

  it("polls on the configured interval", async () => {
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(api, "fetchWorkflowRuns")
      .mockResolvedValue([sampleItem("wf-poll")]);
    renderHook(() => useWorkflowRuns(1000));
    await act(async () => {
      await Promise.resolve();
    });
    const base = fetch.mock.calls.length;
    expect(base).toBeGreaterThanOrEqual(1);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(fetch.mock.calls.length).toBe(base + 1);
  });

  it("refetches when the workflow runs list query is invalidated", async () => {
    const fetch = vi
      .spyOn(api, "fetchWorkflowRuns")
      .mockResolvedValue([sampleItem("wf-a")]);
    const { unmount } = renderHook(() => useWorkflowRuns(60_000));
    await waitFor(() => expect(fetch).toHaveBeenCalled());
    const base = fetch.mock.calls.length;
    await act(async () => {
      await invalidateWorkflowRunsList();
    });
    expect(fetch.mock.calls.length).toBe(base + 1);
    unmount();
  });
});
