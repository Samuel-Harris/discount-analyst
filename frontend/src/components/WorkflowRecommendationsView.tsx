import { useMemo, useState } from "react";

import type { TickerRunDetail, WorkflowRunDetailResponse } from "../api";
import { sortedWorkflowRuns } from "../graph/buildGraphLayout";
import { recommendationRatingClassNames } from "../graph/laneRatingChipStyles";
import { laneStatusDisplay } from "../utils/laneStatusDisplay";

export interface WorkflowRecommendationsViewProps {
  detail: WorkflowRunDetailResponse;
}

type SortKey =
  | "ticker"
  | "company_name"
  | "status"
  | "final_rating"
  | "decision_type"
  | "entry_path";

function formatDecisionType(
  dt: TickerRunDetail["decision_type"],
): string {
  if (dt === "arbiter") return "Arbiter";
  if (dt === "sentinel_rejection") return "Sentinel";
  return "—";
}

function formatEntryPath(path: TickerRunDetail["entry_path"]): string {
  return path === "surveyor" ? "Surveyor" : "Profiler";
}

function compareStrings(a: string, b: string, dir: "asc" | "desc"): number {
  const cmp = a.localeCompare(b, undefined, { sensitivity: "base" });
  return dir === "asc" ? cmp : -cmp;
}

function compareRows(
  a: TickerRunDetail,
  b: TickerRunDetail,
  key: SortKey,
  dir: "asc" | "desc",
): number {
  switch (key) {
    case "ticker":
      return compareStrings(a.ticker, b.ticker, dir);
    case "company_name":
      return compareStrings(a.company_name, b.company_name, dir);
    case "status":
      return compareStrings(
        laneStatusDisplay(a).label,
        laneStatusDisplay(b).label,
        dir,
      );
    case "final_rating": {
      const as = a.final_rating ?? "";
      const bs = b.final_rating ?? "";
      return compareStrings(as, bs, dir);
    }
    case "decision_type": {
      const as = formatDecisionType(a.decision_type);
      const bs = formatDecisionType(b.decision_type);
      return compareStrings(as, bs, dir);
    }
    case "entry_path":
      return compareStrings(a.entry_path, b.entry_path, dir);
    default:
      return 0;
  }
}

export function WorkflowRecommendationsView({
  detail,
}: WorkflowRecommendationsViewProps) {
  const [filter, setFilter] = useState("");
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const baseOrder = useMemo(
    () => sortedWorkflowRuns(detail.runs),
    [detail.runs],
  );

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return baseOrder;
    return baseOrder.filter(
      (r) =>
        r.ticker.toLowerCase().includes(q) ||
        r.company_name.toLowerCase().includes(q),
    );
  }, [baseOrder, filter]);

  const rows = useMemo(() => {
    if (!sortKey) return filtered;
    return [...filtered].sort((a, b) => compareRows(a, b, sortKey, sortDir));
  }, [filtered, sortKey, sortDir]);

  const onSortHeader = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const sortIndicator = (key: SortKey): string => {
    if (sortKey !== key) return "";
    return sortDir === "asc" ? " ▲" : " ▼";
  };

  return (
    <div className="recommendations-view">
      <div className="recommendations-toolbar">
        <label className="recommendations-filter">
          <span className="recommendations-filter-label">Filter</span>
          <input
            type="search"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Ticker or company…"
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <button
          type="button"
          className="btn-ghost recommendations-reset-sort"
          onClick={() => setSortKey(null)}
          disabled={sortKey === null}
        >
          Graph lane order
        </button>
        <span className="recommendations-count">
          {rows.length} of {detail.runs.length} lane(s)
        </span>
      </div>

      <div className="recommendations-table-wrap">
        <table className="recommendations-table">
          <caption className="sr-only">
            Final ratings and lane status for workflow {detail.id}
          </caption>
          <thead>
            <tr>
              <th scope="col">
                <button
                  type="button"
                  className="recommendations-th-btn"
                  onClick={() => onSortHeader("ticker")}
                >
                  Ticker{sortIndicator("ticker")}
                </button>
              </th>
              <th scope="col">
                <button
                  type="button"
                  className="recommendations-th-btn"
                  onClick={() => onSortHeader("company_name")}
                >
                  Company{sortIndicator("company_name")}
                </button>
              </th>
              <th scope="col">
                <button
                  type="button"
                  className="recommendations-th-btn"
                  onClick={() => onSortHeader("entry_path")}
                >
                  Entry{sortIndicator("entry_path")}
                </button>
              </th>
              <th scope="col">
                <button
                  type="button"
                  className="recommendations-th-btn"
                  onClick={() => onSortHeader("status")}
                >
                  Lane status{sortIndicator("status")}
                </button>
              </th>
              <th scope="col">
                <button
                  type="button"
                  className="recommendations-th-btn"
                  onClick={() => onSortHeader("final_rating")}
                >
                  Rating{sortIndicator("final_rating")}
                </button>
              </th>
              <th scope="col">
                <button
                  type="button"
                  className="recommendations-th-btn"
                  onClick={() => onSortHeader("decision_type")}
                >
                  Verdict source{sortIndicator("decision_type")}
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((run) => {
              const laneSt = laneStatusDisplay(run);
              return (
              <tr key={run.id}>
                <td className="recommendations-mono">{run.ticker}</td>
                <td>{run.company_name}</td>
                <td>{formatEntryPath(run.entry_path)}</td>
                <td>
                  <span
                    className={`recommendations-status recommendations-status--${laneSt.tone}`}
                    title={laneSt.title}
                  >
                    {laneSt.label}
                  </span>
                </td>
                <td>
                  <span
                    className={recommendationRatingClassNames(
                      run.final_rating,
                      run.decision_type,
                    )}
                  >
                    {run.final_rating ?? "Pending"}
                  </span>
                </td>
                <td>{formatDecisionType(run.decision_type)}</td>
              </tr>
            );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
