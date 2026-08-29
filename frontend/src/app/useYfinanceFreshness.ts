import { useEffect, useState } from "react";

import { fetchDashboardStatus, type YfinanceFreshnessResponse } from "@/api";

export function useYfinanceFreshness(): YfinanceFreshnessResponse | null {
  const [freshness, setFreshness] = useState<YfinanceFreshnessResponse | null>(
    null,
  );

  useEffect(() => {
    const controller = new AbortController();
    void fetchDashboardStatus({ signal: controller.signal })
      .then((status) => {
        if (!controller.signal.aborted) {
          setFreshness(status.yfinance);
        }
      })
      .catch(() => {
        /* Keep the dashboard usable if the status endpoint is unavailable. */
      });
    return () => controller.abort();
  }, []);

  return freshness;
}
