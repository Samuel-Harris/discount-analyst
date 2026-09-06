import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  AllocationPosition,
  PortfolioAllocation,
  TickerRunDetail,
  WorkflowRunDetailResponse,
} from "@/api";
import * as api from "@/api";
import { resetQueryInvalidationRegistryForTests } from "@/lib/server-state/invalidation";
import { WorkflowRecommendationsView } from "./WorkflowRecommendationsView";

function lane(overrides: Partial<TickerRunDetail> = {}): TickerRunDetail {
  return {
    id: "run-1",
    ticker: "SEED1.L",
    company_name: "Seed One plc",
    entry_path: "profiler",
    status: "completed",
    final_rating: "HOLD",
    decision_type: "rating_table",
    agent_executions: [],
    ...overrides,
  };
}

function detail(
  overrides: Partial<WorkflowRunDetailResponse> = {},
): WorkflowRunDetailResponse {
  return {
    id: "wf-seed",
    started_at: "2026-09-06T12:00:00Z",
    completed_at: "2026-09-06T12:10:00Z",
    status: "completed",
    is_mock: true,
    error_message: null,
    can_retry_failed_agents: false,
    surveyor_execution: {
      id: "wfe-surveyor",
      agent_name: "surveyor",
      status: "completed",
      started_at: null,
      completed_at: null,
    },
    curator_execution: {
      id: "wfe-curator",
      agent_name: "curator",
      status: "pending",
      started_at: null,
      completed_at: null,
    },
    runs: [
      lane(),
      lane({
        id: "run-2",
        ticker: "SEED2.L",
        company_name: "Seed Two plc",
        entry_path: "surveyor",
        final_rating: "SELL",
        decision_type: "sentinel_rejection",
      }),
    ],
    ...overrides,
  };
}

function position(
  overrides: Partial<AllocationPosition> & Pick<AllocationPosition, "ticker">,
): AllocationPosition {
  return {
    company_name: overrides.ticker,
    source_run_id: `run-${overrides.ticker}`,
    is_existing_position: false,
    current_weight_pct: 0,
    target_weight_pct: 0,
    acceptable_weight_low_pct: 0,
    acceptable_weight_high_pct: 0,
    action: "avoid",
    rationale: `${overrides.ticker} rationale`,
    policy: { kind: "investable" },
    ...overrides,
  };
}

function seedAllocation(): PortfolioAllocation {
  return {
    allocation_date: "2026-09-06",
    portfolio_rationale:
      "Seed book: reduce the existing name and avoid the rejection.",
    cash: {
      current_weight_pct: 20,
      target_weight_pct: 85,
      acceptable_weight_low_pct: 84,
      acceptable_weight_high_pct: 86,
      rationale: "Residual seed capital held in cash.",
    },
    positions: [
      position({
        ticker: "SEED1.L",
        company_name: "SEED1.L",
        is_existing_position: true,
        current_weight_pct: 80,
        target_weight_pct: 15,
        acceptable_weight_low_pct: 14,
        acceptable_weight_high_pct: 15,
        action: "reduce",
        rationale: "Seed concentrated existing holding.",
      }),
      position({
        ticker: "SEED2.L",
        company_name: "Seed Two plc",
        is_existing_position: false,
        current_weight_pct: 0,
        target_weight_pct: 0,
        acceptable_weight_low_pct: 0,
        acceptable_weight_high_pct: 0,
        action: "avoid",
        rationale: "Seed Sentinel rejection is forced zero.",
      }),
    ],
    shared_risk_clusters: [],
  };
}

describe("WorkflowRecommendationsView", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    resetQueryInvalidationRegistryForTests();
  });

  it("shows pending Curator copy and no book chrome", () => {
    const fetch = vi.spyOn(api, "fetchWorkflowAllocation");
    render(
      <WorkflowRecommendationsView
        detail={detail({ curator_execution: null })}
      />,
    );
    expect(
      screen.getByText("Curator has not started yet."),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Portfolio" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/Cash /)).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Lane ratings" }),
    ).toBeInTheDocument();
    expect(screen.getByText("SEED1.L")).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("renders the Curator book above the ratings table when allocation is present", async () => {
    vi.spyOn(api, "fetchWorkflowAllocation").mockResolvedValue(
      seedAllocation(),
    );
    render(
      <WorkflowRecommendationsView
        detail={detail({
          curator_execution: {
            id: "wfe-curator",
            agent_name: "curator",
            status: "completed",
            started_at: null,
            completed_at: null,
          },
        })}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Portfolio" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Seed book: reduce the existing name and avoid the rejection.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Cash 20\.0% → 85\.0%/)).toBeInTheDocument();
    expect(screen.getByText(/84\.0–86\.0%/)).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Clusters" }),
    ).not.toBeInTheDocument();

    const book = screen
      .getByRole("heading", { name: "Portfolio" })
      .closest("section");
    expect(book).not.toBeNull();
    const bookTable = within(book as HTMLElement).getByRole("table");
    const seed1Row = within(bookTable)
      .getAllByRole("row")
      .find(
        (row) =>
          row.classList.contains("recommendations-book-position") &&
          within(row).getAllByRole("cell")[0]?.textContent === "SEED1.L",
      );
    const seed2Row = within(bookTable)
      .getAllByRole("row")
      .find(
        (row) =>
          row.classList.contains("recommendations-book-position") &&
          within(row).getAllByRole("cell")[0]?.textContent === "SEED2.L",
      );
    expect(seed1Row).toBeDefined();
    expect(seed2Row).toBeUndefined();
    expect(
      within(seed1Row as HTMLElement).getByText("Holding"),
    ).toBeInTheDocument();
    expect(
      within(seed1Row as HTMLElement).getByText("Reduce"),
    ).toBeInTheDocument();
    expect(
      within(seed1Row as HTMLElement).getByText("80.0% → 15.0%"),
    ).toBeInTheDocument();
    expect(
      within(seed1Row as HTMLElement).getByText("14.0–15.0%"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Lane ratings" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Final ratings and lane status for workflow wf-seed"),
    ).toBeInTheDocument();
    expect(screen.getByText("2 of 2 lane(s)")).toBeInTheDocument();
  });

  it("keeps the ratings filter off the book", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "fetchWorkflowAllocation").mockResolvedValue(
      seedAllocation(),
    );
    render(
      <WorkflowRecommendationsView
        detail={detail({
          curator_execution: {
            id: "wfe-curator",
            agent_name: "curator",
            status: "completed",
            started_at: null,
            completed_at: null,
          },
        })}
      />,
    );
    await screen.findByRole("heading", { name: "Portfolio" });
    await user.type(screen.getByRole("searchbox", { name: "Filter" }), "SEED2");
    expect(screen.getByText("1 of 2 lane(s)")).toBeInTheDocument();
    const book = screen
      .getByRole("heading", { name: "Portfolio" })
      .closest("section");
    expect(
      within(book as HTMLElement).getAllByText("SEED1.L").length,
    ).toBeGreaterThan(0);
    expect(
      within(book as HTMLElement).queryByText("SEED2.L"),
    ).not.toBeInTheDocument();
  });

  it("shows the 404 status line when allocation is missing", async () => {
    vi.spyOn(api, "fetchWorkflowAllocation").mockResolvedValue(null);
    render(
      <WorkflowRecommendationsView
        detail={detail({
          curator_execution: {
            id: "wfe-curator",
            agent_name: "curator",
            status: "completed",
            started_at: null,
            completed_at: null,
          },
        })}
      />,
    );
    await waitFor(() => {
      expect(
        screen.getByText("Curator completed, allocation not available yet."),
      ).toBeInTheDocument();
    });
    expect(
      screen.queryByRole("heading", { name: "Portfolio" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Lane ratings" }),
    ).toBeInTheDocument();
  });
});
