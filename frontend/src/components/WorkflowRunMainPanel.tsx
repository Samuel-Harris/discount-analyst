import type { ReactNode } from "react";

import type { WorkflowRunDetailResponse } from "../api";
import type { ConversationTarget } from "../hooks/useConversation";
import type { WorkflowMainView } from "../hooks/useWorkflowRunNavigation";
import { PipelineGraph } from "./PipelineGraph";
import { UiStateText } from "./UiStateText";
import { WorkflowRunDetailHeader } from "./WorkflowRunDetailHeader";
import { WorkflowRecommendationsView } from "./WorkflowRecommendationsView";

export interface WorkflowRunMainPanelProps {
  selectedId: string | null;
  detail: WorkflowRunDetailResponse | null;
  detailLoading: boolean;
  detailError: string | null;
  sidebarCollapsed: boolean;
  workflowActionError: string | null;
  cancelPending: boolean;
  launchForm: ReactNode;
  mainView: WorkflowMainView;
  onOpenRecommendations: () => void;
  onOpenPipeline: () => void;
  onOpenConversation: (target: ConversationTarget, title: string) => void;
  onRequestDeleteRun: (id: string) => void;
  onRequestCancelRun: (id: string) => void;
}

export function WorkflowRunMainPanel({
  selectedId,
  detail,
  detailLoading,
  detailError,
  sidebarCollapsed,
  workflowActionError,
  cancelPending,
  launchForm,
  mainView,
  onOpenRecommendations,
  onOpenPipeline,
  onOpenConversation,
  onRequestDeleteRun,
  onRequestCancelRun,
}: WorkflowRunMainPanelProps) {
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
        {detail && !detailLoading ? (
          <>
            <WorkflowRunDetailHeader
              detail={detail}
              onRequestDelete={() => onRequestDeleteRun(detail.id)}
              onRequestCancel={() => onRequestCancelRun(detail.id)}
              cancelPending={cancelPending}
              mainView={mainView}
              onOpenRecommendations={onOpenRecommendations}
              onOpenPipeline={onOpenPipeline}
            />
            {mainView === "pipeline" ? (
              <PipelineGraph
                detail={detail}
                onOpenConversation={onOpenConversation}
              />
            ) : (
              <WorkflowRecommendationsView detail={detail} />
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
