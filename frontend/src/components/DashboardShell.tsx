import { useCallback, useEffect, useState } from "react";

import { deleteWorkflowRun } from "../api";
import { invalidateWorkflowRunsList } from "../serverState";
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
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    setDeleteError(null);
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
      setDeleteError(null);
      try {
        await deleteWorkflowRun(id);
        if (selectedId === id) selectRunFromSidebar(null);
        await invalidateWorkflowRunsList();
      } catch (e) {
        setDeleteError(
          e instanceof Error ? e.message : "Delete failed; try again.",
        );
      }
    },
    [selectedId, selectRunFromSidebar],
  );

  const onLaunched = useCallback((workflowRunId: string) => {
    openLaunchedRun(workflowRunId);
  }, [openLaunchedRun]);

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
        deleteError={deleteError}
        launchForm={launchForm}
        mainView={mainView}
        onOpenRecommendations={openRecommendations}
        onOpenPipeline={openPipeline}
        onOpenConversation={openConversation}
        onRequestDeleteRun={(id) => void handleDelete(id)}
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
