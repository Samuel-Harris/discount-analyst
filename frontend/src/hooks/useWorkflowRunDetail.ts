import { useCallback, useEffect, useRef, useState } from "react";

import { fetchWorkflowRunDetail, type WorkflowRunDetailResponse } from "../api";

const DEFAULT_POLL_MS = 2500;

export function useWorkflowRunDetail(
  workflowRunId: string | null,
  pollMs: number = DEFAULT_POLL_MS,
) {
  const [detail, setDetail] = useState<WorkflowRunDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(true);
  const latestWorkflowId = useRef<string | null>(workflowRunId);
  latestWorkflowId.current = workflowRunId;

  const load = useCallback(
    async (opts: { showSpinner: boolean }) => {
      const captureId = workflowRunId;
      if (!captureId) {
        setDetail(null);
        setError(null);
        setLoading(false);
        return;
      }
      if (opts.showSpinner) setLoading(true);
      try {
        const data = await fetchWorkflowRunDetail(captureId);
        if (!mounted.current) return;
        if (latestWorkflowId.current !== captureId) return;
        setDetail(data);
        setError(null);
      } catch (e) {
        if (!mounted.current) return;
        if (latestWorkflowId.current !== captureId) return;
        if (opts.showSpinner) {
          setDetail(null);
          setError(e instanceof Error ? e.message : "Failed to load workflow");
        }
      } finally {
        if (
          mounted.current &&
          opts.showSpinner &&
          latestWorkflowId.current === captureId
        ) {
          setLoading(false);
        }
      }
    },
    [workflowRunId],
  );

  const refresh = useCallback(async () => {
    await load({ showSpinner: false });
  }, [load]);

  useEffect(() => {
    mounted.current = true;
    void load({ showSpinner: true });
    return () => {
      mounted.current = false;
    };
  }, [load]);

  useEffect(() => {
    if (!workflowRunId) return () => undefined;
    const id = window.setInterval(
      () => void load({ showSpinner: false }),
      pollMs,
    );
    return () => window.clearInterval(id);
  }, [load, workflowRunId, pollMs]);

  return { detail, loading, error, refresh };
}
