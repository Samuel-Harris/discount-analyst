import type { ReactNode } from "react";

import type { WorkflowRunDetailResponse } from "../api";
import type { ConversationTarget } from "../hooks/useConversation";
import { PipelineGraph } from "./PipelineGraph";
import { UiStateText } from "./UiStateText";
import { WorkflowRunDetailHeader } from "./WorkflowRunDetailHeader";

export interface WorkflowRunMainPanelProps {
  selectedId: string | null;
  detail: WorkflowRunDetailResponse | null;
  detailLoading: boolean;
  detailError: string | null;
  sidebarCollapsed: boolean;
  deleteError: string | null;
  launchForm: ReactNode;
  onOpenConversation: (target: ConversationTarget, title: string) => void;
  onRequestDeleteRun: (id: string) => void;
}

export function WorkflowRunMainPanel({
  selectedId,
  detail,
  detailLoading,
  detailError,
  sidebarCollapsed,
  deleteError,
  launchForm,
  onOpenConversation,
  onRequestDeleteRun,
}: WorkflowRunMainPanelProps) {
  return (
    <main className="main-panel">
      <div className="main-body">
        {deleteError ? (
          <div className="main-panel-alert" role="alert">
            <UiStateText tone="error" as="p">
              {deleteError}
            </UiStateText>
          </div>
        ) : null}
        {detail && !detailLoading ? (
          <>
            <WorkflowRunDetailHeader
              detail={detail}
              onRequestDelete={() => onRequestDeleteRun(detail.id)}
            />
            <PipelineGraph
              detail={detail}
              onOpenConversation={onOpenConversation}
            />
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
