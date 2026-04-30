import { useCallback, useEffect, useMemo, useState } from "react";

export type WorkflowMainView = "pipeline" | "recommendations";

export type WorkflowRunNavState = {
  selectedId: string | null;
  mainView: WorkflowMainView;
};

/** Parse `window.location.search` or an equivalent query string (with or without `?`). */
export function parseWorkflowRunUrlSearch(search: string): WorkflowRunNavState {
  const trimmed = search.startsWith("?") ? search.slice(1) : search;
  const params = new URLSearchParams(trimmed);
  const run = params.get("run");
  const viewRaw = params.get("view");
  const mainView: WorkflowMainView =
    viewRaw === "recommendations" && run ? "recommendations" : "pipeline";
  return {
    selectedId: run && run.length > 0 ? run : null,
    mainView,
  };
}

/** Build `?run=…&view=…` (or empty string when nothing selected). */
export function formatWorkflowRunUrlSearch(state: WorkflowRunNavState): string {
  const params = new URLSearchParams();
  if (state.selectedId) params.set("run", state.selectedId);
  if (state.mainView === "recommendations" && state.selectedId) {
    params.set("view", "recommendations");
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

function pushUrl(state: WorkflowRunNavState): void {
  const search = formatWorkflowRunUrlSearch(state);
  const path = `${window.location.pathname}${search}`;
  window.history.pushState(state, "", path);
}

function replaceUrl(state: WorkflowRunNavState): void {
  const search = formatWorkflowRunUrlSearch(state);
  const path = `${window.location.pathname}${search}`;
  window.history.replaceState(state, "", path);
}

/**
 * Selected workflow run plus pipeline vs recommendations table view, kept in sync
 * with `?run=` and `?view=recommendations` for deep links and the back button.
 */
export function useWorkflowRunNavigation(): {
  selectedId: string | null;
  mainView: WorkflowMainView;
  selectRunFromSidebar: (id: string | null) => void;
  openLaunchedRun: (workflowRunId: string) => void;
  openRecommendations: () => void;
  openPipeline: () => void;
} {
  const [state, setState] = useState<WorkflowRunNavState>(() =>
    typeof window === "undefined"
      ? { selectedId: null, mainView: "pipeline" }
      : parseWorkflowRunUrlSearch(window.location.search),
  );

  useEffect(() => {
    const onPopState = () => {
      setState(parseWorkflowRunUrlSearch(window.location.search));
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const selectRunFromSidebar = useCallback((id: string | null) => {
    const next: WorkflowRunNavState = {
      selectedId: id,
      mainView: "pipeline",
    };
    setState(next);
    replaceUrl(next);
  }, []);

  const openLaunchedRun = useCallback((workflowRunId: string) => {
    const next: WorkflowRunNavState = {
      selectedId: workflowRunId,
      mainView: "pipeline",
    };
    setState(next);
    replaceUrl(next);
  }, []);

  const openRecommendations = useCallback(() => {
    setState((prev) => {
      if (!prev.selectedId) return prev;
      const next: WorkflowRunNavState = {
        selectedId: prev.selectedId,
        mainView: "recommendations",
      };
      pushUrl(next);
      return next;
    });
  }, []);

  const openPipeline = useCallback(() => {
    setState((prev) => {
      if (!prev.selectedId) return prev;
      const next: WorkflowRunNavState = {
        selectedId: prev.selectedId,
        mainView: "pipeline",
      };
      pushUrl(next);
      return next;
    });
  }, []);

  return useMemo(
    () => ({
      selectedId: state.selectedId,
      mainView: state.mainView,
      selectRunFromSidebar,
      openLaunchedRun,
      openRecommendations,
      openPipeline,
    }),
    [
      state.selectedId,
      state.mainView,
      selectRunFromSidebar,
      openLaunchedRun,
      openRecommendations,
      openPipeline,
    ],
  );
}
