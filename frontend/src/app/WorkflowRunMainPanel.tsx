import { useMemo, type ReactNode } from "react";

import type { WorkflowRunDetailResponse } from "@/api";
import { UiStateText } from "@/components/UiStateText";
import { PipelineGraph } from "@/features/pipeline-graph/PipelineGraph";
import { sortedWorkflowRuns } from "@/features/pipeline-graph/tickerRunOrder";
import { WorkflowRecommendationsView } from "@/features/workflow-runs/WorkflowRecommendationsView";
import { WorkflowRunDetailHeader } from "@/features/workflow-runs/WorkflowRunDetailHeader";
import type { WorkflowMainView } from "@/features/workflow-runs/useWorkflowRunNavigation";
import type { ConversationTarget } from "@/types/conversationTarget";

export interface WorkflowRunMainPanelProps {
  selectedId: string | null;
  detail: WorkflowRunDetailResponse | null;
  detailLoading: boolean;
  detailError: string | null;
  sidebarCollapsed: boolean;
  workflowActionError: string | null;
  cancelPending: boolean;
  retryFailedAgentsPending: boolean;
  launchForm: ReactNode;
  mainView: WorkflowMainView;
  onOpenRecommendations: () => void;
  onOpenPipeline: () => void;
  onOpenConversation: (target: ConversationTarget, title: string) => void;
  onRequestDeleteRun: (id: string) => void;
  onRequestCancelRun: (id: string) => void;
  onRequestRetryFailedAgents: (id: string) => void;
}

export function WorkflowRunMainPanel({
  selectedId,
  detail,
  detailLoading,
  detailError,
  sidebarCollapsed,
  workflowActionError,
  cancelPending,
  retryFailedAgentsPending,
  launchForm,
  mainView,
  onOpenRecommendations,
  onOpenPipeline,
  onOpenConversation,
  onRequestDeleteRun,
  onRequestCancelRun,
  onRequestRetryFailedAgents,
}: WorkflowRunMainPanelProps) {
  const detailWithLaneOrder = useMemo(() => {
    if (!detail) return null;
    return { ...detail, runs: sortedWorkflowRuns(detail.runs) };
  }, [detail]);

  return (
    <main className="main-panel">
      <div className="main-body">
        {workflowActionError ? (
          <div className="main-panel-alert" role="alert">
            <UiStateText tone="error" as="p">
              {workflowActionError}
            </UiStateText>
          </div>
        ) : null}
        {detailWithLaneOrder && !detailLoading ? (
          <>
            <WorkflowRunDetailHeader
              detail={detailWithLaneOrder}
              onRequestDelete={() => onRequestDeleteRun(detailWithLaneOrder.id)}
              onRequestCancel={() => onRequestCancelRun(detailWithLaneOrder.id)}
              onRequestRetryFailedAgents={() =>
                onRequestRetryFailedAgents(detailWithLaneOrder.id)
              }
              cancelPending={cancelPending}
              retryFailedAgentsPending={retryFailedAgentsPending}
              mainView={mainView}
              onOpenRecommendations={onOpenRecommendations}
              onOpenPipeline={onOpenPipeline}
            />
            {mainView === "pipeline" ? (
              <PipelineGraph
                detail={detailWithLaneOrder}
                onOpenConversation={onOpenConversation}
              />
            ) : (
              <WorkflowRecommendationsView detail={detailWithLaneOrder} />
            )}
          </>
        ) : detailLoading && selectedId ? (
          <div className="placeholder-main">
            <UiStateText tone="loading" as="p">
              Loading workflow…
            </UiStateText>
          </div>
        ) : detailError && selectedId ? (
          <div className="placeholder-main">
            <UiStateText tone="error" as="p">
              {detailError}
            </UiStateText>
          </div>
        ) : (
          <div className="placeholder-main">
            <UiStateText tone="muted" as="p">
              Select a workflow run from the sidebar, or launch a new one
              {sidebarCollapsed ? " below" : " from the launch panel"}.
            </UiStateText>
          </div>
        )}
      </div>
      {sidebarCollapsed ? launchForm : null}
    </main>
  );
}
