import { useCallback, useMemo } from "react";

import {
  fetchWorkflowAllocation,
  type ExecutionStatusApi,
  type PortfolioAllocation,
} from "@/api";
import { workflowAllocationKey } from "@/lib/server-state/queryKeys";
import { usePollingQuery } from "@/lib/server-state/usePollingQuery";

const DEFAULT_POLL_MS = 2500;

const INACTIVE_ALLOCATION_KEY = "workflowRuns:allocation:__inactive__";

type AllocationEnvelope = {
  allocation: PortfolioAllocation | null;
};

export function useWorkflowAllocation(
  workflowRunId: string,
  curatorStatus: ExecutionStatusApi | null,
  pollMs: number = DEFAULT_POLL_MS,
) {
  const enabled = curatorStatus === "completed";

  const queryKey = useMemo(
    () =>
      enabled ? workflowAllocationKey(workflowRunId) : INACTIVE_ALLOCATION_KEY,
    [enabled, workflowRunId],
  );

  const fetcher = useCallback(
    async (signal: AbortSignal): Promise<AllocationEnvelope> => ({
      allocation: await fetchWorkflowAllocation(workflowRunId, { signal }),
    }),
    [workflowRunId],
  );

  const discardDataOnError = useCallback(
    (mode: "initial" | "silent") => mode === "initial",
    [],
  );

  const {
    data: envelope,
    loading,
    error,
    refresh,
  } = usePollingQuery<AllocationEnvelope>({
    queryKey,
    enabled,
    pollMs,
    fetcher,
    defaultErrorMessage: "Could not load allocation.",
    loadingStartsTrueWhenEnabled: false,
    discardDataOnError,
  });

  const waitingForAllocation = enabled && !error && envelope === null;

  return {
    data: envelope?.allocation ?? null,
    loading: loading || waitingForAllocation,
    error,
    refresh,
  };
}
