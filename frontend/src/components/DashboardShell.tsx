import { useCallback, useEffect, useState } from "react";

import { cancelWorkflowRun, deleteWorkflowRun, retryFailedAgents } from "../api";
import {
  invalidateWorkflowRunDetail,
  invalidateWorkflowRunsList,
} from "../serverState";
import { AgentPanel } from "./AgentPanel";
import { RunPipelineForm } from "./RunPipelineForm";
import { Sidebar } from "./Sidebar";
import {
  useConversation,
  type ConversationTarget,
} from "../hooks/useConversation";
import { useWorkflowRunDetail } from "../hooks/useWorkflowRunDetail";
import { useWorkflowRunNavigation } from "../hooks/useWorkflowRunNavigation";
import { useWorkflowRuns } from "../hooks/useWorkflowRuns";
import { AppHeader } from "./layout/AppHeader";
import { WorkflowRunMainPanel } from "./WorkflowRunMainPanel";

export function DashboardShell() {
  const { items, loading, error } = useWorkflowRuns();
  const {
    selectedId,
    mainView,
    selectRunFromSidebar,
    openLaunchedRun,
    openRecommendations,
    openPipeline,
  } = useWorkflowRunNavigation();
  const {
    detail,
    loading: detailLoading,
    error: detailError,
  } = useWorkflowRunDetail(selectedId);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [workflowActionError, setWorkflowActionError] = useState<string | null>(
    null,
  );
  const [cancelPending, setCancelPending] = useState(false);
  const [retryFailedAgentsPending, setRetryFailedAgentsPending] = useState(false);

  useEffect(() => {
    setWorkflowActionError(null);
  }, [selectedId]);

  const conversation = useConversation();
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelTitle, setPanelTitle] = useState("");

  const closePanel = useCallback(() => {
    setPanelOpen(false);
    conversation.clear();
  }, [conversation]);

  const openConversation = useCallback(
    (target: ConversationTarget, title: string) => {
      setPanelTitle(title);
      setPanelOpen(true);
      void conversation.load(target);
    },
    [conversation],
  );

  const handleDelete = useCallback(
    async (id: string) => {
      const ok = window.confirm("Delete this mock workflow run?");
      if (!ok) return;
      setWorkflowActionError(null);
      try {
        await deleteWorkflowRun(id);
        if (selectedId === id) selectRunFromSidebar(null);
        await invalidateWorkflowRunsList();
      } catch (e) {
        setWorkflowActionError(
          e instanceof Error ? e.message : "Delete failed; try again.",
        );
      }
    },
    [selectedId, selectRunFromSidebar],
  );

  const handleCancel = useCallback(async (id: string) => {
    const ok = window.confirm("Cancel this workflow?");
    if (!ok) return;
    setWorkflowActionError(null);
    setCancelPending(true);
    try {
      await cancelWorkflowRun(id);
      await Promise.all([
        invalidateWorkflowRunsList(),
        invalidateWorkflowRunDetail(id),
      ]);
    } catch (e) {
      setWorkflowActionError(
        e instanceof Error ? e.message : "Cancel failed; try again.",
      );
    } finally {
      setCancelPending(false);
    }
  }, []);

  const handleRetryFailedAgents = useCallback(async (id: string) => {
    setWorkflowActionError(null);
    setRetryFailedAgentsPending(true);
    try {
      await retryFailedAgents(id);
      await Promise.all([
        invalidateWorkflowRunsList(),
        invalidateWorkflowRunDetail(id),
      ]);
    } catch (e) {
      setWorkflowActionError(
        e instanceof Error ? e.message : "Retry failed; try again.",
      );
    } finally {
      setRetryFailedAgentsPending(false);
    }
  }, []);

  const onLaunched = useCallback(
    (workflowRunId: string) => {
      openLaunchedRun(workflowRunId);
    },
    [openLaunchedRun],
  );

  const launchForm = <RunPipelineForm onLaunched={onLaunched} />;

  return (
    <div className="app-shell">
      <AppHeader listError={error} listLoading={loading} />

      <Sidebar
        items={items}
        selectedId={selectedId}
        onSelect={selectRunFromSidebar}
        onDelete={(id) => void handleDelete(id)}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((c) => !c)}
        footer={sidebarCollapsed ? undefined : launchForm}
      />

      <WorkflowRunMainPanel
        selectedId={selectedId}
        detail={detail}
        detailLoading={detailLoading}
        detailError={detailError}
        sidebarCollapsed={sidebarCollapsed}
        workflowActionError={workflowActionError}
        cancelPending={cancelPending}
        retryFailedAgentsPending={retryFailedAgentsPending}
        launchForm={launchForm}
        mainView={mainView}
        onOpenRecommendations={openRecommendations}
        onOpenPipeline={openPipeline}
        onOpenConversation={openConversation}
        onRequestDeleteRun={(id) => void handleDelete(id)}
        onRequestCancelRun={(id) => void handleCancel(id)}
        onRequestRetryFailedAgents={(id) => void handleRetryFailedAgents(id)}
      />

      <AgentPanel
        open={panelOpen}
        title={panelTitle}
        loading={conversation.loading}
        error={conversation.error}
        data={conversation.data}
        onClose={closePanel}
      />
    </div>
  );
}
