import { describe, expect, it } from "vitest";

import {
  marginOfSafetyPct,
  parseAppraiserOutput,
} from "./parseAppraiserOutput";

const validOutput = {
  ticker: "ABC.L",
  company_name: "ABC plc",
  valuation_date: "2026-06-04",
  summary: "Mock summary.",
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
    distribution_reasoning: "Mock reasoning.",
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
} as const;

describe("parseAppraiserOutput", () => {
  it("parses valid Appraiser JSON", () => {
    const parsed = parseAppraiserOutput(JSON.stringify(validOutput));
    expect(parsed?.ticker).toBe("ABC.L");
    expect(parsed?.valuation_distribution.expected_intrinsic_value).toBe(3.8);
  });

  it("returns null for invalid JSON", () => {
    expect(parseAppraiserOutput("{not json")).toBeNull();
  });

  it("returns null for partial shape", () => {
    expect(parseAppraiserOutput(JSON.stringify({ ticker: "X" }))).toBeNull();
  });
});

describe("marginOfSafetyPct", () => {
  it("matches backend margin formula", () => {
    expect(marginOfSafetyPct(10, 12)).toBeCloseTo(20);
  });
});
