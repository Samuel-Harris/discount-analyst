import type { ReactNode } from "react";

import type { WorkflowRunListItem } from "../api";

function shortId(id: string): string {
  return id.length > 18 ? `${id.slice(0, 10)}…${id.slice(-6)}` : id;
}

function formatWhen(iso: string): string {
  try {
    return new Date(iso).toLocaleString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export interface SidebarProps {
  items: WorkflowRunListItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  footer?: ReactNode;
}

export function Sidebar({
  items,
  selectedId,
  onSelect,
  onDelete,
  collapsed,
  onToggleCollapse,
  footer,
}: SidebarProps) {
  if (collapsed) {
    return (
      <aside className="sidebar" style={{ width: 44, minWidth: 44 }}>
        <div className="sidebar-toolbar">
          <button
            type="button"
            className="toggle"
            onClick={onToggleCollapse}
            title="Expand runs"
          >
            »
          </button>
        </div>
      </aside>
    );
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-toolbar">
        <span style={{ fontSize: 11, color: "var(--text-dim)" }}>
          Workflow runs
        </span>
        <button
          type="button"
          className="toggle"
          onClick={onToggleCollapse}
          title="Collapse sidebar"
        >
          «
        </button>
      </div>
      <div className="workflow-list">
        {items.map((w) => (
          <div
            key={w.id}
            style={{ display: "flex", gap: 4, alignItems: "stretch" }}
          >
            <button
              type="button"
              className={`workflow-row${w.id === selectedId ? " active" : ""}`}
              onClick={() => onSelect(w.id)}
              style={{ flex: 1 }}
            >
              <div className="row-title">
                <span className={`status-pill ${w.status}`}>{w.status}</span>
                {w.is_mock ? (
                  <span className="badge mock" title="Mock workflow">
                    mock
                  </span>
                ) : null}
              </div>
              <div className="id-short" title={w.id}>
                {shortId(w.id)}
              </div>
              <div className="counts">
                {formatWhen(w.started_at)} · runs {w.completed_ticker_run_count}
                /{w.ticker_run_count}
                {w.failed_ticker_run_count > 0
                  ? ` · failed ${w.failed_ticker_run_count}`
                  : ""}
              </div>
            </button>
            {w.is_mock ? (
              <button
                type="button"
                className="btn-ghost"
                title="Delete mock workflow"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(w.id);
                }}
              >
                del
              </button>
            ) : null}
          </div>
        ))}
      </div>
      {footer}
    </aside>
  );
}
