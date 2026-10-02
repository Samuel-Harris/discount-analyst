import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { AllocationPosition, PortfolioAllocation } from "@/api";
import { WorkflowRecommendationsBook } from "./WorkflowRecommendationsBook";

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
    ...overrides,
  };
}

function allocation(
  overrides: Partial<PortfolioAllocation> = {},
): PortfolioAllocation {
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
    ],
    shared_risk_clusters: [],
    ...overrides,
  };
}

describe("WorkflowRecommendationsBook", () => {
  it("orders positions by target weight descending then ticker", () => {
    render(
      <WorkflowRecommendationsBook
        portfolioValueGbp={10_000}
        allocation={allocation({
          positions: [
            position({
              ticker: "LOW.L",
              target_weight_pct: 5,
              action: "enter",
            }),
            position({
              ticker: "ZZZ.L",
              target_weight_pct: 20,
              action: "enter",
            }),
            position({
              ticker: "AAA.L",
              target_weight_pct: 20,
              action: "enter",
            }),
          ],
        })}
      />,
    );
    const rows = screen
      .getAllByRole("row")
      .filter((row) => row.classList.contains("recommendations-book-position"));
    const tickers = rows.map(
      (row) => within(row).getAllByRole("cell")[0]?.textContent,
    );
    expect(tickers).toEqual(["AAA.L", "ZZZ.L", "LOW.L"]);
  });

  it("renders clusters as label and member tickers only", () => {
    render(
      <WorkflowRecommendationsBook
        portfolioValueGbp={10_000}
        allocation={allocation({
          shared_risk_clusters: [
            {
              label: "Energy pair",
              mechanism: "shared oil beta",
              allocation_effect: "cap combined weight",
              member_tickers: ["AAA.L", "BBB.L"],
            },
          ],
        })}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "Clusters" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Energy pair/)).toBeInTheDocument();
    expect(screen.getByText("AAA.L")).toBeInTheDocument();
    expect(screen.getByText("BBB.L")).toBeInTheDocument();
    expect(screen.queryByText("shared oil beta")).not.toBeInTheDocument();
    expect(screen.queryByText("cap combined weight")).not.toBeInTheDocument();
  });

  it("omits the clusters heading when the list is empty", () => {
    render(
      <WorkflowRecommendationsBook
        portfolioValueGbp={10_000}
        allocation={allocation()}
      />,
    );
    expect(
      screen.queryByRole("heading", { name: "Clusters" }),
    ).not.toBeInTheDocument();
  });

  it("omits unheld Avoid names and keeps holdings and new entries", () => {
    render(
      <WorkflowRecommendationsBook
        portfolioValueGbp={10_000}
        allocation={allocation({
          positions: [
            position({
              ticker: "HOLD.L",
              is_existing_position: true,
              current_weight_pct: 80,
              target_weight_pct: 15,
              action: "reduce",
            }),
            position({
              ticker: "SKIP.L",
              is_existing_position: false,
              target_weight_pct: 0,
              action: "avoid",
            }),
            position({
              ticker: "NEW.L",
              is_existing_position: false,
              target_weight_pct: 8,
              action: "enter",
            }),
            position({
              ticker: "EXIT.L",
              is_existing_position: true,
              current_weight_pct: 10,
              target_weight_pct: 0,
              action: "exit",
            }),
          ],
        })}
      />,
    );
    const rows = screen
      .getAllByRole("row")
      .filter((row) => row.classList.contains("recommendations-book-position"));
    const tickers = rows.map(
      (row) => within(row).getAllByRole("cell")[0]?.textContent,
    );
    expect(tickers).toEqual(["HOLD.L", "NEW.L", "EXIT.L"]);
    expect(screen.queryByText("SKIP.L")).not.toBeInTheDocument();
  });

  it("shows the recommended sterling size from the input portfolio value", () => {
    render(
      <WorkflowRecommendationsBook
        portfolioValueGbp={10_000}
        allocation={allocation()}
      />,
    );

    expect(
      screen.getByRole("columnheader", { name: "Recommended (£)" }),
    ).toBeInTheDocument();
    const seedRow = screen
      .getAllByRole("row")
      .find((row) => row.classList.contains("recommendations-book-position"));
    expect(seedRow).toBeDefined();
    expect(
      within(seedRow as HTMLElement).getByText("£1,500.00"),
    ).toBeInTheDocument();
    expect(screen.getByText(/Cash 20\.0% → 85\.0%/)).toHaveTextContent(
      "£8,500.00",
    );
  });

  it("shows an em dash when the run has no stored portfolio value", () => {
    render(
      <WorkflowRecommendationsBook
        portfolioValueGbp={null}
        allocation={allocation()}
      />,
    );

    const seedRow = screen
      .getAllByRole("row")
      .find((row) => row.classList.contains("recommendations-book-position"));
    expect(within(seedRow as HTMLElement).getByText("—")).toBeInTheDocument();
    expect(screen.getByText(/Cash 20\.0% → 85\.0%/)).toHaveTextContent("—");
  });
});
