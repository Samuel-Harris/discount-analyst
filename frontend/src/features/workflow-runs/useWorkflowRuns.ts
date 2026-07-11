import { useCallback } from "react";

import { fetchWorkflowRuns, type WorkflowRunListItem } from "@/api";
import { WORKFLOW_RUNS_LIST_KEY } from "@/lib/server-state/queryKeys";
import { usePollingQuery } from "@/lib/server-state/usePollingQuery";

const DEFAULT_POLL_MS = 3000;

export function useWorkflowRuns(pollMs: number = DEFAULT_POLL_MS) {
  const fetcher = useCallback(
    (signal: AbortSignal) => fetchWorkflowRuns({ signal }),
    [],
  );

  const discardDataOnError = useCallback(() => false, []);

  const { data, loading, error, refresh } = usePollingQuery<
    WorkflowRunListItem[]
  >({
    queryKey: WORKFLOW_RUNS_LIST_KEY,
    enabled: true,
    pollMs,
    fetcher,
    defaultErrorMessage: "Failed to load workflow runs",
    loadingStartsTrueWhenEnabled: true,
    discardDataOnError,
  });

  return { items: data ?? [], loading, error, refresh };
}
