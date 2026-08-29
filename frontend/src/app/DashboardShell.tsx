import { useCallback, useState } from "react";

import { YfinanceOutdatedBanner } from "@/components/YfinanceOutdatedBanner";
import { AgentPanel } from "@/features/agent-conversation/AgentPanel";
import { useAgentConversationPanel } from "@/features/agent-conversation/useAgentConversationPanel";
import { RunPipelineForm } from "@/features/workflow-runs/RunPipelineForm";
import { Sidebar } from "@/features/workflow-runs/Sidebar";
import { useWorkflowRunActions } from "@/features/workflow-runs/useWorkflowRunActions";
import { useWorkflowRunDetail } from "@/features/workflow-runs/useWorkflowRunDetail";
import { useWorkflowRunNavigation } from "@/features/workflow-runs/useWorkflowRunNavigation";
import { useWorkflowRuns } from "@/features/workflow-runs/useWorkflowRuns";
import { AppHeader } from "./layout/AppHeader";
import { useYfinanceFreshness } from "./useYfinanceFreshness";
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
  const clearSelection = useCallback(
    () => selectRunFromSidebar(null),
    [selectRunFromSidebar],
  );
  const {
    actionError,
    cancelPending,
    retryFailedAgentsPending,
    deleteRun,
    cancelRun,
    retryFailed,
  } = useWorkflowRunActions({
    selectedId,
    clearSelection,
  });
  const conversationPanel = useAgentConversationPanel();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const yfinance = useYfinanceFreshness();

  const onLaunched = useCallback(
    (workflowRunId: string) => {
      openLaunchedRun(workflowRunId);
    },
    [openLaunchedRun],
  );

  const launchForm = <RunPipelineForm onLaunched={onLaunched} />;

  return (
    <div className="app-shell">
      <div className="app-top">
        <AppHeader listError={error} listLoading={loading} />
        {yfinance?.is_outdated && yfinance.latest_version ? (
          <YfinanceOutdatedBanner
            installedVersion={yfinance.installed_version}
            latestVersion={yfinance.latest_version}
          />
        ) : null}
      </div>

      <Sidebar
        items={items}
        selectedId={selectedId}
        onSelect={selectRunFromSidebar}
        onDelete={(id) => void deleteRun(id)}
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
        workflowActionError={actionError}
        cancelPending={cancelPending}
        retryFailedAgentsPending={retryFailedAgentsPending}
        launchForm={launchForm}
        mainView={mainView}
        onOpenRecommendations={openRecommendations}
        onOpenPipeline={openPipeline}
        onOpenConversation={conversationPanel.openConversation}
        onRequestDeleteRun={(id) => void deleteRun(id)}
        onRequestCancelRun={(id) => void cancelRun(id)}
        onRequestRetryFailedAgents={(id) => void retryFailed(id)}
      />

      <AgentPanel
        open={conversationPanel.open}
        title={conversationPanel.title}
        agentName={conversationPanel.agentName}
        loading={conversationPanel.loading}
        error={conversationPanel.error}
        data={conversationPanel.data}
        onClose={conversationPanel.close}
      />
    </div>
  );
}
