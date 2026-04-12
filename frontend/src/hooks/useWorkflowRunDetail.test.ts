import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { WorkflowRunDetailResponse } from "../api";
import * as api from "../api";
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
    expect(fetch).toHaveBeenCalledWith("wf-99");
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
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(result.current.loading).toBe(false);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(result.current.loading).toBe(false);
  });
});
