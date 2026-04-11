import { useCallback, useEffect, useRef, useState } from "react";

import { fetchWorkflowRuns, type WorkflowRunListItem } from "../api";

const DEFAULT_POLL_MS = 3000;

export function useWorkflowRuns(pollMs: number = DEFAULT_POLL_MS) {
  const [items, setItems] = useState<WorkflowRunListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(true);

  const refresh = useCallback(async () => {
    try {
      const data = await fetchWorkflowRuns();
      if (!mounted.current) return;
      setItems(data);
      setError(null);
    } catch (e) {
      if (!mounted.current) return;
      setError(e instanceof Error ? e.message : "Failed to load workflow runs");
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    void refresh();
    const id = window.setInterval(() => void refresh(), pollMs);
    return () => {
      mounted.current = false;
      window.clearInterval(id);
    };
  }, [refresh, pollMs]);

  return { items, loading, error, refresh };
}
