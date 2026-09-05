import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createWorkflowRun,
  fetchPortfolio,
  type PortfolioPositionInput,
} from "@/api";
import { UiStateText } from "@/components/UiStateText";
import { invalidateWorkflowRunsList } from "@/lib/server-state/invalidation";

type PositionDraft = {
  ticker: string;
  valueGbp: string;
};

type LaunchFormState = {
  positions: PositionDraft[];
  cashGbp: string;
  suggestions: string[];
  draft: string;
};

function emptyPosition(): PositionDraft {
  return { ticker: "", valueGbp: "" };
}

const INITIAL_FORM: LaunchFormState = {
  positions: [emptyPosition()],
  cashGbp: "0",
  suggestions: [],
  draft: "",
};

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

function parsePounds(raw: string): number | null {
  const trimmed = raw.trim();
  if (trimmed === "") return null;
  const value = Number(trimmed);
  if (!Number.isFinite(value) || value < 0) return null;
  return value;
}

function isLaunchFormEmpty(form: LaunchFormState): boolean {
  const positionsEmpty = form.positions.every(
    (row) => row.ticker.trim() === "" && row.valueGbp.trim() === "",
  );
  const cashDefault = form.cashGbp.trim() === "" || form.cashGbp.trim() === "0";
  return (
    positionsEmpty &&
    cashDefault &&
    form.suggestions.length === 0 &&
    form.draft.trim() === ""
  );
}

function formatPounds(value: number): string {
  return value.toLocaleString("en-GB", {
    style: "currency",
    currency: "GBP",
  });
}

function formatWeightPct(value: number, total: number): string {
  if (total <= 0) return "—";
  return `${((100 * value) / total).toFixed(1)}%`;
}

function formatLaunchSummary(
  holdingCount: number,
  extraCount: number,
  total: number,
): string {
  const holdingsLabel =
    holdingCount === 1 ? "1 holding" : `${holdingCount} holdings`;
  const extrasLabel =
    extraCount === 0
      ? ""
      : extraCount === 1
        ? " · 1 extra"
        : ` · ${extraCount} extra`;
  return `Launch · ${holdingsLabel} · ${formatPounds(total)}${extrasLabel}`;
}

function positionsForSubmit(rows: PositionDraft[]): PortfolioPositionInput[] {
  const submitted: PortfolioPositionInput[] = [];
  for (const row of rows) {
    const ticker = row.ticker.trim();
    const valueGbp = parsePounds(row.valueGbp);
    if (!ticker || valueGbp === null) continue;
    submitted.push({ ticker, value_gbp: valueGbp });
  }
  return submitted;
}

export interface RunPipelineFormProps {
  onLaunched: (workflowRunId: string) => void;
  hidden?: boolean;
}

const deployEnv = import.meta.env.VITE_DEPLOY_ENV;
const mockModeLocked = deployEnv !== "PROD";

export function RunPipelineForm({
  onLaunched,
  hidden = false,
}: RunPipelineFormProps) {
  const [expanded, setExpanded] = useState(false);
  const [form, setForm] = useState<LaunchFormState>(INITIAL_FORM);
  const [isMock, setIsMock] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const ledger = await fetchPortfolio();
        if (cancelled) return;
        setForm((prev) => {
          if (!isLaunchFormEmpty(prev)) return prev;
          const positions =
            ledger.positions.length > 0
              ? ledger.positions.map((row) => ({
                  ticker: row.ticker,
                  valueGbp: String(row.value_gbp),
                }))
              : [emptyPosition()];
          return {
            positions,
            cashGbp: String(ledger.cash_gbp),
            suggestions: [...new Set(ledger.suggestion_tickers)],
            draft: "",
          };
        });
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
    setForm((prev) => {
      const parsed = parseTickers(prev.draft);
      if (parsed.length === 0) return prev;
      return {
        ...prev,
        suggestions: [...new Set([...prev.suggestions, ...parsed])],
        draft: "",
      };
    });
  }, []);

  const preview = useMemo(() => {
    const holdingValues = form.positions.map((row) => {
      const ticker = row.ticker.trim();
      const value = parsePounds(row.valueGbp);
      if (!ticker || value === null) return 0;
      return value;
    });
    const holdingsTotal = holdingValues.reduce((sum, value) => sum + value, 0);
    const cash = parsePounds(form.cashGbp) ?? 0;
    const total = holdingsTotal + cash;
    return { holdingValues, cash, total };
  }, [form.cashGbp, form.positions]);

  const summary = useMemo(() => {
    const holdingCount = positionsForSubmit(form.positions).length;
    const extraCount = tickersForSubmit(form.suggestions, form.draft).length;
    return formatLaunchSummary(holdingCount, extraCount, preview.total);
  }, [form.draft, form.positions, form.suggestions, preview.total]);

  const submit = useCallback(async () => {
    setFormError(null);
    const positions = positionsForSubmit(form.positions);
    const suggestionTickers = tickersForSubmit(form.suggestions, form.draft);
    const cashGbp = parsePounds(form.cashGbp) ?? 0;
    setSubmitting(true);
    try {
      const res = await createWorkflowRun({
        positions,
        cash_gbp: cashGbp,
        suggestion_tickers: suggestionTickers,
        is_mock: mockModeLocked || isMock,
      });
      onLaunched(res.workflow_run_id);
      await invalidateWorkflowRunsList();
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Launch failed");
    } finally {
      setSubmitting(false);
    }
  }, [form, isMock, onLaunched]);

  return (
    <aside
      className={`launch-rail${expanded ? " is-expanded" : " is-collapsed"}`}
      aria-label="Launch workflow"
      hidden={hidden}
    >
      {expanded ? (
        <div className="launch-rail-toolbar">
          <h2>Launch workflow</h2>
          <button
            type="button"
            className="toggle"
            title="Collapse launch panel"
            aria-label="Collapse launch panel"
            aria-expanded="true"
            onClick={() => setExpanded(false)}
          >
            »
          </button>
        </div>
      ) : (
        <button
          type="button"
          className="launch-rail-expand"
          title={summary}
          aria-label={`Expand launch panel: ${summary}`}
          aria-expanded="false"
          onClick={() => setExpanded(true)}
        >
          {summary}
        </button>
      )}
      {expanded ? (
        <div className="launch-panel">
          <h3>Current positions</h3>
      <div
        className={`positions-table-wrap${submitting ? " is-disabled" : ""}`}
      >
        <table className="positions-table">
          <thead>
            <tr>
              <th scope="col">Ticker</th>
              <th scope="col">Value (£)</th>
              <th scope="col">Weight</th>
              <th scope="col">
                <span className="sr-only">Remove</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {form.positions.map((row, index) => (
              <tr key={index}>
                <td>
                  <input
                    type="text"
                    value={row.ticker}
                    onChange={(event) => {
                      const ticker = event.target.value;
                      setForm((prev) => ({
                        ...prev,
                        positions: prev.positions.map((current, rowIndex) =>
                          rowIndex === index ? { ...current, ticker } : current,
                        ),
                      }));
                    }}
                    placeholder="CBOX.L"
                    aria-label={`Position ticker ${index + 1}`}
                    disabled={submitting}
                  />
                </td>
                <td>
                  <input
                    type="number"
                    min={0}
                    step="0.01"
                    value={row.valueGbp}
                    onChange={(event) => {
                      const valueGbp = event.target.value;
                      setForm((prev) => ({
                        ...prev,
                        positions: prev.positions.map((current, rowIndex) =>
                          rowIndex === index
                            ? { ...current, valueGbp }
                            : current,
                        ),
                      }));
                    }}
                    placeholder="0.00"
                    aria-label={`Position value in pounds ${index + 1}`}
                    disabled={submitting}
                  />
                </td>
                <td className="positions-weight">
                  {formatWeightPct(
                    preview.holdingValues[index] ?? 0,
                    preview.total,
                  )}
                </td>
                <td>
                  <button
                    type="button"
                    className="positions-remove"
                    aria-label={`Remove position ${index + 1}`}
                    disabled={submitting || form.positions.length === 1}
                    onClick={() =>
                      setForm((prev) => ({
                        ...prev,
                        positions:
                          prev.positions.length === 1
                            ? prev.positions
                            : prev.positions.filter(
                                (_row, rowIndex) => rowIndex !== index,
                              ),
                      }))
                    }
                  >
                    ×
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="positions-footer">
        <button
          type="button"
          className="positions-add"
          onClick={() =>
            setForm((prev) => ({
              ...prev,
              positions: [...prev.positions, emptyPosition()],
            }))
          }
          disabled={submitting}
        >
          Add position
        </button>
        <label className="cash-field">
          Cash (£)
          <input
            type="number"
            min={0}
            step="0.01"
            value={form.cashGbp}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, cashGbp: event.target.value }))
            }
            aria-label="Cash in pounds"
            disabled={submitting}
          />
        </label>
        <span className="positions-cash-weight">
          {preview.total <= 0
            ? "100.0%"
            : formatWeightPct(preview.cash, preview.total)}
        </span>
        <span className="positions-total">
          Total {formatPounds(preview.total)}
        </span>
      </div>

      <h3>Also analyse</h3>
      <div className={`ticker-input-wrap${submitting ? " is-disabled" : ""}`}>
        {form.suggestions.map((ticker) => (
          <span key={ticker} className="ticker-pill">
            {ticker}
            <button
              type="button"
              className="ticker-pill-remove"
              aria-label={`Remove ${ticker}`}
              disabled={submitting}
              onClick={() =>
                setForm((prev) => ({
                  ...prev,
                  suggestions: prev.suggestions.filter(
                    (item) => item !== ticker,
                  ),
                }))
              }
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          value={form.draft}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, draft: event.target.value }))
          }
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              commitDraft();
            } else if (
              event.key === "Backspace" &&
              form.draft === "" &&
              form.suggestions.length > 0
            ) {
              event.preventDefault();
              setForm((prev) => ({
                ...prev,
                suggestions: prev.suggestions.slice(0, -1),
              }));
            }
          }}
          placeholder="CBOX.L — press Enter"
          aria-label="Also analyse"
          disabled={submitting}
        />
      </div>
      <div className="row">
        <label className="mock">
          <input
            type="checkbox"
            checked={mockModeLocked || isMock}
            onChange={(event) => setIsMock(event.target.checked)}
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
          {formError ? (
            <UiStateText tone="error" as="p" className="launch-panel-form-status">
              {formError}
            </UiStateText>
          ) : null}
        </div>
      ) : null}
    </aside>
  );
}
