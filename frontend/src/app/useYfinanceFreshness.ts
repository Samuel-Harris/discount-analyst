import { useEffect, useState } from "react";

import { fetchDashboardStatus, type YfinanceFreshnessResponse } from "@/api";

export const YFINANCE_STATUS_RETRY_MS = 2_000;

export function useYfinanceFreshness(): YfinanceFreshnessResponse | null {
  const [freshness, setFreshness] = useState<YfinanceFreshnessResponse | null>(
    null,
  );

  useEffect(() => {
    const controller = new AbortController();
    let retryTimer: ReturnType<typeof setTimeout> | undefined;

    const load = () => {
      void fetchDashboardStatus({ signal: controller.signal })
        .then((status) => {
          if (!controller.signal.aborted) {
            setFreshness(status.yfinance);
          }
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) {
            return;
          }
          if (error instanceof Error && error.name === "AbortError") {
            return;
          }
          retryTimer = setTimeout(load, YFINANCE_STATUS_RETRY_MS);
        });
    };

    load();
    return () => {
      controller.abort();
      if (retryTimer !== undefined) {
        clearTimeout(retryTimer);
      }
    };
  }, []);

  return freshness;
}
