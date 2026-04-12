import { useCallback, useEffect, useState } from "react";

import { createWorkflowRun, fetchPortfolio } from "../api";

function parseTickers(raw: string): string[] {
  const parts = raw
    .split(/[\n,]+/)
    .map((s) => s.trim())
    .filter(Boolean);
  return [...new Set(parts)];
}

function tickersForSubmit(tickers: string[], draft: string): string[] {
  const fromDraft = draft.trim() ? parseTickers(draft) : [];
  return [...new Set([...tickers, ...fromDraft])];
}

export interface RunPipelineFormProps {
  onLaunched: (workflowRunId: string) => void;
  onRefreshList: () => void;
}

const deployEnv = import.meta.env.VITE_DEPLOY_ENV;
const mockModeLocked = deployEnv !== "PROD";

export function RunPipelineForm({
  onLaunched,
  onRefreshList,
}: RunPipelineFormProps) {
  const [tickers, setTickers] = useState<string[]>([]);
  const [draft, setDraft] = useState("");
  const [isMock, setIsMock] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const { portfolio_tickers } = await fetchPortfolio();
        if (cancelled) return;
        if (portfolio_tickers.length > 0) {
          setTickers((prev) =>
            prev.length === 0 ? [...new Set(portfolio_tickers)] : prev,
          );
        }
      } catch {
        /* latest portfolio optional */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (mockModeLocked) setIsMock(true);
  }, [mockModeLocked]);

  const commitDraft = useCallback(() => {
    const parsed = parseTickers(draft);
    if (parsed.length === 0) return;
    setTickers((prev) => [...new Set([...prev, ...parsed])]);
    setDraft("");
  }, [draft]);

  const submit = useCallback(async () => {
    setFormError(null);
    const list = tickersForSubmit(tickers, draft);
    setSubmitting(true);
    try {
      const res = await createWorkflowRun({
        portfolio_tickers: list,
        is_mock: mockModeLocked || isMock,
      });
      onLaunched(res.workflow_run_id);
      onRefreshList();
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Launch failed");
    } finally {
      setSubmitting(false);
    }
  }, [tickers, draft, isMock, onLaunched, onRefreshList]);

  return (
    <div className="launch-panel">
      <h2>Launch workflow</h2>
      <p className="meta">
        Surveyor discovery runs in the background; each portfolio ticker starts
        an immediate Profiler pipeline. Press Enter after a ticker to add it as
        a pill (draft text is still included when you start).
      </p>
      <div className={`ticker-input-wrap${submitting ? " is-disabled" : ""}`}>
        {tickers.map((t) => (
          <span key={t} className="ticker-pill">
            {t}
            <button
              type="button"
              className="ticker-pill-remove"
              aria-label={`Remove ${t}`}
              disabled={submitting}
              onClick={() => setTickers((prev) => prev.filter((x) => x !== t))}
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              commitDraft();
            } else if (
              e.key === "Backspace" &&
              draft === "" &&
              tickers.length > 0
            ) {
              e.preventDefault();
              setTickers((prev) => prev.slice(0, -1));
            }
          }}
          placeholder="CBOX.L — press Enter"
          aria-label="Portfolio tickers"
          disabled={submitting}
        />
      </div>
      <div className="row">
        <label className="mock">
          <input
            type="checkbox"
            checked={mockModeLocked || isMock}
            onChange={(e) => setIsMock(e.target.checked)}
            disabled={submitting || mockModeLocked}
          />
          {mockModeLocked
            ? "Mock mode (required in DEV; no live LLM; slower simulated steps)"
            : "Mock mode (no live LLM; slower simulated steps)"}
        </label>
        <button
          type="button"
          className="submit"
          onClick={() => void submit()}
          disabled={submitting}
        >
          {submitting ? "Starting…" : "Start workflow"}
        </button>
      </div>
      {formError ? <p className="err">{formError}</p> : null}
    </div>
  );
}
