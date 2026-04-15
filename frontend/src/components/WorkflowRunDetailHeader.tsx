import type { WorkflowRunDetailResponse } from "../api";
import { formatWhen } from "../utils/formatWhen";
import { UiStateText } from "./UiStateText";

export interface WorkflowRunDetailHeaderProps {
  detail: WorkflowRunDetailResponse;
  onRequestDelete: () => void;
}

export function WorkflowRunDetailHeader({
  detail,
  onRequestDelete,
}: WorkflowRunDetailHeaderProps) {
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
          transcripts open the conversation panel.
        </div>
      </div>
      <div className="detail-header-actions">
        {detail.is_mock ? (
          <button
            type="button"
            className="btn-ghost"
            onClick={() => onRequestDelete()}
          >
            Delete mock run
          </button>
        ) : null}
      </div>
    </div>
  );
}
