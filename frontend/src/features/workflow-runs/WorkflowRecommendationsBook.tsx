import { Fragment, useMemo } from "react";

import type { PortfolioAllocation } from "@/api";
import {
  formatBookMembership,
  formatRebalanceAction,
  formatWeightBand,
  formatWeightChange,
  isDisplayedBookPosition,
} from "./allocationDisplay";
import { recommendationActionClassNames } from "./recommendationActionStyles";

export interface WorkflowRecommendationsBookProps {
  allocation: PortfolioAllocation;
}

function comparePositions(
  a: PortfolioAllocation["positions"][number],
  b: PortfolioAllocation["positions"][number],
): number {
  if (b.target_weight_pct !== a.target_weight_pct) {
    return b.target_weight_pct - a.target_weight_pct;
  }
  return a.ticker.localeCompare(b.ticker);
}

export function WorkflowRecommendationsBook({
  allocation,
}: WorkflowRecommendationsBookProps) {
  const positions = useMemo(
    () =>
      allocation.positions
        .filter(isDisplayedBookPosition)
        .sort(comparePositions),
    [allocation.positions],
  );
  const allocationDate = allocation.allocation_date.slice(0, 10);
  const { cash } = allocation;

  return (
    <section className="recommendations-book-body" aria-labelledby="recommendations-book-heading">
      <header className="recommendations-book-header">
        <h2 id="recommendations-book-heading">Portfolio</h2>
        <p className="recommendations-book-date">{allocationDate}</p>
      </header>
      <p className="recommendations-book-rationale">
        {allocation.portfolio_rationale}
      </p>
      <p className="recommendations-book-cash">
        <span>
          {`Cash ${formatWeightChange(cash.current_weight_pct, cash.target_weight_pct)} (${formatWeightBand(
            cash.acceptable_weight_low_pct,
            cash.acceptable_weight_high_pct,
          )})`}
        </span>
        <span className="recommendations-book-cash-rationale">
          {cash.rationale}
        </span>
      </p>
      <table className="recommendations-table recommendations-book-table">
        <thead>
          <tr>
            <th scope="col">Ticker</th>
            <th scope="col">Company</th>
            <th scope="col">Book</th>
            <th scope="col">Action</th>
            <th scope="col">Weight</th>
            <th scope="col">Band</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((position) => (
            <Fragment key={position.ticker}>
              <tr className="recommendations-book-position">
                <td className="recommendations-mono">{position.ticker}</td>
                <td>{position.company_name}</td>
                <td>{formatBookMembership(position.is_existing_position)}</td>
                <td>
                  <span className={recommendationActionClassNames(position.action)}>
                    {formatRebalanceAction(position.action)}
                  </span>
                </td>
                <td className="recommendations-mono">
                  {formatWeightChange(
                    position.current_weight_pct,
                    position.target_weight_pct,
                  )}
                </td>
                <td className="recommendations-mono">
                  {formatWeightBand(
                    position.acceptable_weight_low_pct,
                    position.acceptable_weight_high_pct,
                  )}
                </td>
              </tr>
              <tr className="recommendations-book-rationale-row">
                <td colSpan={6}>{position.rationale}</td>
              </tr>
            </Fragment>
          ))}
        </tbody>
      </table>
      {allocation.shared_risk_clusters.length > 0 ? (
        <div className="recommendations-book-clusters">
          <h3>Clusters</h3>
          <ul>
            {allocation.shared_risk_clusters.map((cluster) => (
              <li key={cluster.label}>
                {cluster.label}:{" "}
                {cluster.member_tickers.map((ticker, index) => (
                  <span key={ticker}>
                    {index > 0 ? ", " : null}
                    <span className="recommendations-mono">{ticker}</span>
                  </span>
                ))}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
