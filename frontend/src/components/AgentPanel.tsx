import { useEffect } from "react";

import type { ConversationResponse } from "../api";

function formatMessagesJson(raw: string): string {
  try {
    const parsed: unknown = JSON.parse(raw);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return raw;
  }
}

export interface AgentPanelProps {
  open: boolean;
  title: string;
  loading: boolean;
  error: string | null;
  data: ConversationResponse | null;
  onClose: () => void;
}

export function AgentPanel({
  open,
  title,
  loading,
  error,
  data,
  onClose,
}: AgentPanelProps) {
  useEffect(() => {
    if (!open) return () => undefined;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <div
        className="agent-panel-backdrop"
        role="presentation"
        onClick={onClose}
        onKeyDown={(e) => {
          if (e.key === "Escape") onClose();
        }}
      />
      <aside className="agent-panel" aria-label="Agent conversation">
        <header>
          <h2>{title}</h2>
          <button type="button" className="close" onClick={onClose}>
            ×
          </button>
        </header>
        <div className="body">
          {loading ? <p className="err">Loading…</p> : null}
          {error ? <p className="err">{error}</p> : null}
          {!loading && !error && data ? (
            <>
              <section>
                <h3>System prompt</h3>
                <pre>{data.system_prompt}</pre>
              </section>
              <section>
                <h3>Messages</h3>
                <pre>{formatMessagesJson(data.messages_json)}</pre>
              </section>
              <section>
                <h3>Assistant response</h3>
                <pre>{data.assistant_response}</pre>
              </section>
            </>
          ) : null}
        </div>
      </aside>
    </>
  );
}
