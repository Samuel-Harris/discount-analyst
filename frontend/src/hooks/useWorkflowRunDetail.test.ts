import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { WorkflowRunDetailResponse } from "../api";
import * as api from "../api";
import {
  invalidateWorkflowRunDetail,
  resetQueryInvalidationRegistryForTests,
} from "../serverState";
import { useWorkflowRunDetail } from "./useWorkflowRunDetail";

function minimalDetail(id: string): WorkflowRunDetailResponse {
  return {
    id,
    started_at: "2026-04-01T12:00:00Z",
    completed_at: null,
    status: "running",
    is_mock: true,
    error_message: null,
    surveyor_execution: {
      id: "wfe-1",
      agent_name: "surveyor",
      status: "running",
      started_at: null,
      completed_at: null,
    },
    runs: [],
  };
}

describe("useWorkflowRunDetail", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
    resetQueryInvalidationRegistryForTests();
  });

  it("fetches detail for the selected workflow id", async () => {
    const detail = minimalDetail("wf-99");
    const fetch = vi
      .spyOn(api, "fetchWorkflowRunDetail")
      .mockResolvedValue(detail);
    const { result } = renderHook(() => useWorkflowRunDetail("wf-99", 60_000));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(fetch.mock.calls[0][0]).toBe("wf-99");
    expect(result.current.detail?.id).toBe("wf-99");
    expect(result.current.detail?.runs).toEqual([]);
  });

  it("does not fetch when workflow id is null", async () => {
    const fetch = vi.spyOn(api, "fetchWorkflowRunDetail");
    const { result } = renderHook(() => useWorkflowRunDetail(null, 60_000));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(fetch).not.toHaveBeenCalled();
    expect(result.current.detail).toBeNull();
  });

  it("polls detail without toggling loading on refresh", async () => {
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(api, "fetchWorkflowRunDetail")
      .mockResolvedValue(minimalDetail("wf-tick"));
    const { result } = renderHook(() => useWorkflowRunDetail("wf-tick", 500));
    await act(async () => {
      await Promise.resolve();
    });
    const base = fetch.mock.calls.length;
    expect(base).toBeGreaterThanOrEqual(1);
    expect(result.current.loading).toBe(false);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });
    expect(fetch.mock.calls.length).toBe(base + 1);
    expect(result.current.loading).toBe(false);
  });

  it("surfaces background poll failures while retaining the last successful detail", async () => {
    vi.useFakeTimers();
    const good = minimalDetail("wf-poll");
    const fetch = vi
      .spyOn(api, "fetchWorkflowRunDetail")
      .mockResolvedValueOnce(good)
      .mockRejectedValueOnce(new Error("network blip"));
    const { result } = renderHook(() => useWorkflowRunDetail("wf-poll", 500));
    await act(async () => {
      await Promise.resolve();
    });
    expect(result.current.detail?.id).toBe("wf-poll");
    expect(result.current.error).toBeNull();
    const base = fetch.mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });
    expect(fetch.mock.calls.length).toBe(base + 1);
    expect(result.current.detail?.id).toBe("wf-poll");
    expect(result.current.error).toBe("network blip");
    expect(result.current.loading).toBe(false);
  });

  it("clears a poll error after the next successful fetch", async () => {
    vi.useFakeTimers();
    const good = minimalDetail("wf-recover");
    const fetch = vi
      .spyOn(api, "fetchWorkflowRunDetail")
      .mockResolvedValueOnce(good)
      .mockRejectedValueOnce(new Error("blip"))
      .mockResolvedValueOnce({ ...good, status: "completed" });
    const { result } = renderHook(() =>
      useWorkflowRunDetail("wf-recover", 400),
    );
    await act(async () => {
      await Promise.resolve();
    });
    const afterFirst = fetch.mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(400);
    });
    expect(fetch.mock.calls.length).toBe(afterFirst + 1);
    expect(result.current.error).toBe("blip");
    const afterSecond = fetch.mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(400);
    });
    expect(fetch.mock.calls.length).toBe(afterSecond + 1);
    expect(result.current.error).toBeNull();
    expect(result.current.detail?.status).toBe("completed");
  });

  it("refetches when the workflow run detail query is invalidated", async () => {
    const fetch = vi
      .spyOn(api, "fetchWorkflowRunDetail")
      .mockResolvedValue(minimalDetail("wf-inv"));
    const { unmount } = renderHook(() =>
      useWorkflowRunDetail("wf-inv", 60_000),
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
