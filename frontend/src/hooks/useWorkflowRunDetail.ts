import { useCallback, useMemo } from "react";

import { fetchWorkflowRunDetail, type WorkflowRunDetailResponse } from "../api";
import { usePollingQuery, workflowRunDetailKey } from "../serverState";

const DEFAULT_POLL_MS = 2500;

const INACTIVE_DETAIL_KEY = "workflowRuns:detail:__inactive__";

export function useWorkflowRunDetail(
  workflowRunId: string | null,
  pollMs: number = DEFAULT_POLL_MS,
) {
  const enabled = Boolean(workflowRunId);

  const queryKey = useMemo(
    () =>
      workflowRunId ? workflowRunDetailKey(workflowRunId) : INACTIVE_DETAIL_KEY,
    [workflowRunId],
  );

  const fetcher = useCallback(
    (signal: AbortSignal) => {
      if (!workflowRunId) {
        return Promise.reject(new Error("Workflow run id required"));
      }
      return fetchWorkflowRunDetail(workflowRunId, { signal });
    },
    [workflowRunId],
  );

  const discardDataOnError = useCallback(
    (mode: "initial" | "silent") => mode === "initial",
    [],
  );

  const {
    data: detail,
    loading,
    error,
    refresh,
  } = usePollingQuery<WorkflowRunDetailResponse>({
    queryKey,
    enabled,
    pollMs,
    fetcher,
    defaultErrorMessage: "Failed to load workflow",
    loadingStartsTrueWhenEnabled: false,
    discardDataOnError,
  });

  const selectedDetail = detail?.id === workflowRunId ? detail : null;
  const waitingForSelectedDetail = enabled && !error && selectedDetail === null;

  return {
    detail: selectedDetail,
    loading: loading || waitingForSelectedDetail,
    error,
    refresh,
  };
}
