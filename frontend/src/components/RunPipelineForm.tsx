import { useCallback, useEffect, useState } from "react";

import { createWorkflowRun, fetchPortfolio } from "../api";

function parseTickers(raw: string): string[] {
  const parts = raw
    .split(/[\n,]+/)
    .map((s) => s.trim())
    .filter(Boolean);
  return [...new Set(parts)];
}

export interface RunPipelineFormProps {
  onLaunched: (workflowRunId: string) => void;
  onRefreshList: () => void;
}

export function RunPipelineForm({
  onLaunched,
  onRefreshList,
}: RunPipelineFormProps) {
  const [text, setText] = useState("");
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
          setText((prev) =>
            prev.trim() === "" ? portfolio_tickers.join("\n") : prev,
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

  const submit = useCallback(async () => {
    setFormError(null);
    const tickers = parseTickers(text);
    setSubmitting(true);
    try {
      const res = await createWorkflowRun({
        portfolio_tickers: tickers,
        is_mock: isMock,
      });
      onLaunched(res.workflow_run_id);
      onRefreshList();
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Launch failed");
    } finally {
      setSubmitting(false);
    }
  }, [text, isMock, onLaunched, onRefreshList]);

  return (
    <div className="launch-panel">
      <h2>Launch workflow</h2>
      <p className="meta">
        Surveyor discovery runs in the background; each line is a portfolio
        ticker for an immediate Profiler pipeline.
      </p>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="CBOX.L&#10;VTVI"
        aria-label="Portfolio tickers"
        disabled={submitting}
      />
      <div className="row">
        <label className="mock">
          <input
            type="checkbox"
            checked={isMock}
            onChange={(e) => setIsMock(e.target.checked)}
            disabled={submitting}
          />
          Mock mode (no live LLM; slower simulated steps)
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
