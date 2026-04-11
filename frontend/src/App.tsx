import { useCallback, useState } from "react";

import { deleteWorkflowRun } from "./api";
import { AgentPanel } from "./components/AgentPanel";
import { DeployEnvBadge } from "./components/DeployEnvBadge";
import { PipelineGraph } from "./components/PipelineGraph";
import { RunPipelineForm } from "./components/RunPipelineForm";
import { Sidebar } from "./components/Sidebar";
import {
  useConversation,
  type ConversationTarget,
} from "./hooks/useConversation";
import { useWorkflowRunDetail } from "./hooks/useWorkflowRunDetail";
import { useWorkflowRuns } from "./hooks/useWorkflowRuns";

function formatWhen(iso: string): string {
  try {
    return new Date(iso).toLocaleString("en-GB", {
      weekday: "short",
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function App() {
  const { items, loading, error, refresh } = useWorkflowRuns();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const {
    detail,
    loading: detailLoading,
    error: detailError,
  } = useWorkflowRunDetail(selectedId);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

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
      try {
        await deleteWorkflowRun(id);
        if (selectedId === id) setSelectedId(null);
        await refresh();
      } catch (e) {
        window.alert(e instanceof Error ? e.message : "Delete failed");
      }
    },
    [refresh, selectedId],
  );

  const onLaunched = useCallback((workflowRunId: string) => {
    setSelectedId(workflowRunId);
  }, []);

  const launchForm = (
    <RunPipelineForm
      onLaunched={onLaunched}
      onRefreshList={() => void refresh()}
    />
  );

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>Discount Analyst</h1>
          <div className="subtitle">
            Local pipeline dashboard · grouped workflow runs
          </div>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            flexWrap: "wrap",
            justifyContent: "flex-end",
          }}
        >
          <DeployEnvBadge />
          {error ? (
            <span style={{ color: "var(--err)", fontSize: 12 }}>{error}</span>
          ) : loading ? (
            <span className="subtitle">Loading runs…</span>
          ) : null}
        </div>
      </header>

      <Sidebar
        items={items}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onDelete={(id) => void handleDelete(id)}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((c) => !c)}
        footer={sidebarCollapsed ? undefined : launchForm}
      />

      <main className="main-panel">
        <div className="main-body">
          {detail && !detailLoading ? (
            <>
              <div className="detail-header">
                <div>
                  <div
                    style={{
                      marginBottom: 6,
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      flexWrap: "wrap",
                    }}
                  >
                    <span className={`status-pill ${detail.status}`}>
                      {detail.status}
                    </span>
                    {detail.is_mock ? (
                      <span className="badge mock">mock</span>
                    ) : null}
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
                    <div className="lane-hint" style={{ color: "var(--err)" }}>
                      {detail.error_message}
                    </div>
                  ) : null}
                  <div className="lane-hint">
                    {detail.runs.length} ticker lane(s). Completed nodes with
                    stored transcripts open the conversation panel.
                  </div>
                </div>
                <div
                  style={{ display: "flex", gap: 8, alignItems: "flex-start" }}
                >
                  {detail.is_mock ? (
                    <button
                      type="button"
                      className="btn-ghost"
                      onClick={() => void handleDelete(detail.id)}
                    >
                      Delete mock run
                    </button>
                  ) : null}
                </div>
              </div>
              <PipelineGraph
                detail={detail}
                onOpenConversation={openConversation}
              />
            </>
          ) : detailLoading && selectedId ? (
            <div className="placeholder-main">Loading workflow…</div>
          ) : detailError && selectedId ? (
            <div className="placeholder-main" style={{ color: "var(--err)" }}>
              {detailError}
            </div>
          ) : (
            <div className="placeholder-main">
              Select a workflow run from the sidebar, or launch a new one
              {sidebarCollapsed ? " below" : " from the launch panel"}.
            </div>
          )}
        </div>
        {sidebarCollapsed ? launchForm : null}
      </main>

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
