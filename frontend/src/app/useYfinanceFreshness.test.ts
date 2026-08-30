import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as api from "@/api";
import {
  useYfinanceFreshness,
  YFINANCE_STATUS_RETRY_MS,
} from "./useYfinanceFreshness";

const outdated = {
  installed_version: "1.6.0",
  latest_version: "1.7.0",
  is_outdated: true,
};

describe("useYfinanceFreshness", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("returns yfinance freshness from the dashboard status endpoint", async () => {
    vi.spyOn(api, "fetchDashboardStatus").mockResolvedValue({
      yfinance: outdated,
    });
    const { result } = renderHook(() => useYfinanceFreshness());
    await waitFor(() => {
      expect(result.current?.is_outdated).toBe(true);
    });
    expect(result.current).toEqual(outdated);
  });

  it("stays silent while the status endpoint is down", async () => {
    vi.spyOn(api, "fetchDashboardStatus").mockRejectedValue(
      new Error("status unavailable"),
    );
    const { result, unmount } = renderHook(() => useYfinanceFreshness());
    await waitFor(() => {
      expect(api.fetchDashboardStatus).toHaveBeenCalled();
    });
    expect(result.current).toBeNull();
    unmount();
  });

  it("retries after a failed fetch so a reload race can still show the banner", async () => {
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(api, "fetchDashboardStatus")
      .mockRejectedValueOnce(new Error("status unavailable"))
      .mockResolvedValueOnce({ yfinance: outdated });

    const { result } = renderHook(() => useYfinanceFreshness());
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(result.current).toBeNull();
    expect(fetch).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(YFINANCE_STATUS_RETRY_MS);
    });
    expect(result.current).toEqual(outdated);
    expect(fetch).toHaveBeenCalledTimes(2);
  });
});
