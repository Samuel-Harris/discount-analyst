import { useCallback, useEffect, useState } from "react";

import { cancelWorkflowRun, deleteWorkflowRun, retryFailedAgents } from "@/api";
import {
  invalidateWorkflowRunDetail,
  invalidateWorkflowRunsList,
} from "@/lib/server-state/invalidation";

export type UseWorkflowRunActionsOptions = {
  selectedId: string | null;
  clearSelection: () => void;
};

export function useWorkflowRunActions({
  selectedId,
  clearSelection,
}: UseWorkflowRunActionsOptions) {
  const [actionError, setActionError] = useState<string | null>(null);
  const [cancelPending, setCancelPending] = useState(false);
  const [retryFailedAgentsPending, setRetryFailedAgentsPending] =
    useState(false);

  useEffect(() => {
    setActionError(null);
  }, [selectedId]);

  const deleteRun = useCallback(
    async (id: string) => {
      const ok = window.confirm("Delete this mock workflow run?");
      if (!ok) return;
      setActionError(null);
      try {
        await deleteWorkflowRun(id);
        if (selectedId === id) clearSelection();
        await invalidateWorkflowRunsList();
      } catch (e) {
        setActionError(
          e instanceof Error ? e.message : "Delete failed; try again.",
        );
      }
    },
    [selectedId, clearSelection],
  );

  const cancelRun = useCallback(async (id: string) => {
    const ok = window.confirm("Cancel this workflow?");
    if (!ok) return;
    setActionError(null);
    setCancelPending(true);
    try {
      await cancelWorkflowRun(id);
      await Promise.all([
        invalidateWorkflowRunsList(),
        invalidateWorkflowRunDetail(id),
      ]);
    } catch (e) {
      setActionError(
        e instanceof Error ? e.message : "Cancel failed; try again.",
      );
    } finally {
      setCancelPending(false);
    }
  }, []);

  const retryFailed = useCallback(async (id: string) => {
    setActionError(null);
    setRetryFailedAgentsPending(true);
    try {
      await retryFailedAgents(id);
      await Promise.all([
        invalidateWorkflowRunsList(),
        invalidateWorkflowRunDetail(id),
      ]);
    } catch (e) {
      setActionError(
        e instanceof Error ? e.message : "Retry failed; try again.",
      );
    } finally {
      setRetryFailedAgentsPending(false);
    }
  }, []);

  return {
    actionError,
    cancelPending,
    retryFailedAgentsPending,
    deleteRun,
    cancelRun,
    retryFailed,
  };
}
