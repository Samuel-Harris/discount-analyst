import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as api from "@/api";
import { useYfinanceFreshness } from "./useYfinanceFreshness";

describe("useYfinanceFreshness", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns yfinance freshness from the dashboard status endpoint", async () => {
    vi.spyOn(api, "fetchDashboardStatus").mockResolvedValue({
      yfinance: {
        installed_version: "1.6.0",
        latest_version: "1.7.0",
        is_outdated: true,
      },
    });
    const { result } = renderHook(() => useYfinanceFreshness());
    await waitFor(() => {
      expect(result.current?.is_outdated).toBe(true);
    });
    expect(result.current).toEqual({
      installed_version: "1.6.0",
      latest_version: "1.7.0",
      is_outdated: true,
    });
  });

  it("stays silent when the status endpoint fails", async () => {
    vi.spyOn(api, "fetchDashboardStatus").mockRejectedValue(
      new Error("status unavailable"),
    );
    const { result } = renderHook(() => useYfinanceFreshness());
    await waitFor(() => {
      expect(api.fetchDashboardStatus).toHaveBeenCalled();
    });
    expect(result.current).toBeNull();
  });
});
