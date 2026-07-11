import type { IntrinsicValueDistribution } from "./appraiserTypes";
import { marginOfSafetyPct } from "./parseAppraiserOutput";

export interface ValuationDistributionChartProps {
  distribution: IntrinsicValueDistribution;
}

function formatValue(value: number, currency: string): string {
  return `${value.toFixed(2)} ${currency}`;
}

export function ValuationDistributionChart({
  distribution,
}: ValuationDistributionChartProps) {
  const {
    currency,
    current_share_price: current,
    expected_intrinsic_value: expected,
    p10_intrinsic_value: p10,
    p25_intrinsic_value: p25,
    p50_intrinsic_value: p50,
    p75_intrinsic_value: p75,
    p90_intrinsic_value: p90,
  } = distribution;

  const scaleMin = Math.min(p10, current, expected) * 0.98;
  const scaleMax = Math.max(p90, current, expected) * 1.02;
  const span = scaleMax - scaleMin || 1;

  const toPct = (value: number) => ((value - scaleMin) / span) * 100;
  const bandLeft = toPct(p10);
  const bandWidth = toPct(p90) - bandLeft;
  const mos = marginOfSafetyPct(current, expected);

  const tickMarks = [
    { label: "P10", value: p10 },
    { label: "P25", value: p25 },
    { label: "P50", value: p50 },
    { label: "P75", value: p75 },
    { label: "P90", value: p90 },
  ];

  return (
    <div className="valuation-distribution-chart">
      <div className="valuation-chart-legend">
        <dl>
          <div>
            <dt>Current price</dt>
            <dd>{formatValue(current, currency)}</dd>
          </div>
          <div>
            <dt>Expected intrinsic</dt>
            <dd>{formatValue(expected, currency)}</dd>
          </div>
          <div>
            <dt>Margin of safety</dt>
            <dd
              className={
                mos >= 0 ? "valuation-mos-positive" : "valuation-mos-negative"
              }
            >
              {mos >= 0 ? "+" : ""}
              {mos.toFixed(1)}%
            </dd>
          </div>
        </dl>
      </div>
      <div className="valuation-chart-track" aria-hidden="true">
        <div
          className="valuation-chart-band"
          style={{ left: `${bandLeft}%`, width: `${bandWidth}%` }}
          title="P10–P90 range"
        />
        {tickMarks.map((tick) => (
          <span
            key={tick.label}
            className="valuation-chart-tick"
            style={{ left: `${toPct(tick.value)}%` }}
            title={`${tick.label}: ${formatValue(tick.value, currency)}`}
          />
        ))}
        <span
          className="valuation-chart-marker valuation-chart-marker--market"
          style={{ left: `${toPct(current)}%` }}
          title={`Market: ${formatValue(current, currency)}`}
        />
        <span
          className="valuation-chart-marker valuation-chart-marker--expected"
          style={{ left: `${toPct(expected)}%` }}
          title={`Expected: ${formatValue(expected, currency)}`}
        />
      </div>
      <p className="valuation-chart-caption">
        Shaded band: P10–P90 intrinsic value range
      </p>
    </div>
  );
}
