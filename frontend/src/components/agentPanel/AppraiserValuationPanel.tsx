import type { AppraiserOutput } from "./appraiserTypes";
import { ValuationDistributionChart } from "./ValuationDistributionChart";

export interface AppraiserValuationPanelProps {
  output: AppraiserOutput;
}

function formatMethodValue(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return value.toFixed(2);
}

function formatRange(
  low: number | null | undefined,
  high: number | null | undefined,
): string {
  if (low == null || high == null) return "—";
  return `${low.toFixed(2)}–${high.toFixed(2)}`;
}

export function AppraiserValuationPanel({
  output,
}: AppraiserValuationPanelProps) {
  const { valuation_distribution: distribution } = output;
  const qualityClass = `appraiser-quality appraiser-quality--${output.data_quality.toLowerCase()}`;

  return (
    <div className="appraiser-valuation-panel">
      <header className="appraiser-valuation-headline">
        <div>
          <h4>
            {output.company_name}{" "}
            <span className="appraiser-ticker">({output.ticker})</span>
          </h4>
          <p className="appraiser-meta">
            Valuation date: {output.valuation_date}
            <span className={qualityClass}>
              {output.data_quality} data quality
            </span>
          </p>
        </div>
        <p className="appraiser-summary">{output.summary}</p>
      </header>

      <ValuationDistributionChart distribution={distribution} />

      <section className="appraiser-methods">
        <h4>Valuation methods</h4>
        <div className="appraiser-methods-table-wrap agent-panel-prose-table-wrap">
          <table className="appraiser-methods-table">
            <thead>
              <tr>
                <th scope="col">Method</th>
                <th scope="col">Role</th>
                <th scope="col">Value/share</th>
                <th scope="col">Range</th>
                <th scope="col">Weight</th>
              </tr>
            </thead>
            <tbody>
              {output.methods.map((method) => (
                <tr key={`${method.method}-${method.role}`}>
                  <td>{method.method}</td>
                  <td>{method.role}</td>
                  <td>{formatMethodValue(method.value_per_share)}</td>
                  <td>
                    {formatRange(
                      method.low_value_per_share,
                      method.high_value_per_share,
                    )}
                  </td>
                  <td>
                    {method.weight_pct == null
                      ? "—"
                      : `${method.weight_pct.toFixed(1)}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="appraiser-distribution-note">
        <h4>Distribution</h4>
        <p>
          <strong>{distribution.distribution_method}</strong>
        </p>
        <p className="appraiser-distribution-reasoning">
          {distribution.distribution_reasoning}
        </p>
      </section>
    </div>
  );
}
