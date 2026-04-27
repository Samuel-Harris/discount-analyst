import type { WorkflowRunDetailResponse } from "../api";
import type { WorkflowMainView } from "../hooks/useWorkflowRunNavigation";
import { formatWhen } from "../utils/formatWhen";
import { UiStateText } from "./UiStateText";

export interface WorkflowRunDetailHeaderProps {
  detail: WorkflowRunDetailResponse;
  onRequestDelete: () => void;
  onRequestCancel: () => void;
  onRequestRetryFailedAgents: () => void;
  cancelPending: boolean;
  retryFailedAgentsPending: boolean;
  mainView: WorkflowMainView;
  onOpenRecommendations: () => void;
  onOpenPipeline: () => void;
}

export function WorkflowRunDetailHeader({
  detail,
  onRequestDelete,
  onRequestCancel,
  onRequestRetryFailedAgents,
  cancelPending,
  retryFailedAgentsPending,
  mainView,
  onOpenRecommendations,
  onOpenPipeline,
}: WorkflowRunDetailHeaderProps) {
  const isTerminalWorkflow = ["completed", "failed", "cancelled"].includes(
    detail.status,
  );
  const hasFailedAgent =
    detail.surveyor_execution?.status === "failed" ||
    detail.runs.some((run) =>
      run.agent_executions.some((execution) => execution.status === "failed"),
    );
  const canRetryFailedAgents = isTerminalWorkflow && hasFailedAgent;

  return (
    <div className="detail-header">
      <div>
        <div className="detail-header-title-row">
          <span className={`status-pill ${detail.status}`}>
            {detail.status}
          </span>
          {detail.is_mock ? <span className="badge mock">mock</span> : null}
        </div>
        <div className="meta">
          Started {formatWhen(detail.started_at)}
          {detail.completed_at
            ? ` · Completed ${formatWhen(detail.completed_at)}`
            : ""}
        </div>
        <div className="meta" style={{ marginTop: 4 }}>
          id {detail.id}
        </div>
        {detail.error_message ? (
          <UiStateText tone="error" as="div" className="lane-hint">
            {detail.error_message}
          </UiStateText>
        ) : null}
        <div className="lane-hint">
          {detail.runs.length} ticker lane(s). Completed nodes with stored
          transcripts open the conversation panel. Open Recommendations for a
          sortable verdict table (suited to large runs).
        </div>
      </div>
      <div className="detail-header-actions">
        {mainView === "pipeline" ? (
          <button
            type="button"
            className="btn-ghost"
            onClick={() => onOpenRecommendations()}
          >
            Recommendations
          </button>
        ) : (
          <button
            type="button"
            className="btn-ghost"
            onClick={() => onOpenPipeline()}
          >
            Pipeline graph
          </button>
        )}
        {detail.is_mock ? (
          <button
            type="button"
            className="btn-ghost"
            onClick={() => onRequestDelete()}
          >
            Delete mock run
          </button>
        ) : null}
        {detail.status === "running" ? (
          <button
            type="button"
            className="btn-ghost"
            onClick={() => onRequestCancel()}
            disabled={cancelPending}
          >
            {cancelPending ? "Cancelling..." : "Cancel workflow"}
          </button>
        ) : null}
        {canRetryFailedAgents ? (
          <button
            type="button"
            className="btn-ghost"
            onClick={() => onRequestRetryFailedAgents()}
            disabled={retryFailedAgentsPending}
          >
            {retryFailedAgentsPending
              ? "Retrying failed agents..."
              : "Retry all failed agents"}
          </button>
        ) : null}
      </div>
    </div>
  );
}
