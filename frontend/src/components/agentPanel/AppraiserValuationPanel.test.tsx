import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AppraiserValuationPanel } from "./AppraiserValuationPanel";
import type { AppraiserOutput } from "./appraiserTypes";

const fixture: AppraiserOutput = {
  ticker: "ABC.L",
  company_name: "ABC plc",
  valuation_date: "2026-06-04",
  summary: "Undervalued on scenario weighting.",
  valuation_distribution: {
    currency: "GBP",
    current_share_price: 3,
    expected_intrinsic_value: 3.8,
    p10_intrinsic_value: 2.6,
    p25_intrinsic_value: 3.1,
    p50_intrinsic_value: 3.6,
    p75_intrinsic_value: 4.2,
    p90_intrinsic_value: 5,
    distribution_method: "scenario_weighting",
    distribution_reasoning: "Weighted scenarios.",
  },
  methods: [
    {
      method: "scenario_weighting",
      role: "primary",
      value_per_share: 3.8,
      weight_pct: 70,
    },
    {
      method: "comparable_multiples",
      role: "cross_check",
      value_per_share: 3.5,
      weight_pct: 30,
    },
  ],
  data_quality: "Medium",
};

describe("AppraiserValuationPanel", () => {
  it("renders headline, chart legend, and methods table", () => {
    render(<AppraiserValuationPanel output={fixture} />);

    expect(screen.getByText(/ABC plc/)).toBeInTheDocument();
    expect(screen.getByText(/Margin of safety/)).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: "Method" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("cell", { name: "scenario_weighting" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Weighted scenarios/)).toBeInTheDocument();
  });
});
