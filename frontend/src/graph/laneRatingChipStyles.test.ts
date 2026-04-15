import { describe, expect, it } from "vitest";

import type { LaneRatingChipLayout } from "./buildGraphLayout";
import {
  finalRatingToneSlug,
  laneRatingChipClassNames,
  laneRatingChipToneClass,
  recommendationRatingClassNames,
} from "./laneRatingChipStyles";

function chip(
  overrides: Partial<LaneRatingChipLayout>,
): LaneRatingChipLayout {
  return {
    runId: "r1",
    ticker: "TST.L",
    finalRating: null,
    decisionType: null,
    topPx: 100,
    ...overrides,
  };
}

describe("finalRatingToneSlug", () => {
  it("matches laneRatingChipToneClass for rating strings", () => {
    expect(finalRatingToneSlug("BUY")).toBe("buy");
    expect(finalRatingToneSlug(null)).toBe("pending");
  });
});

describe("laneRatingChipToneClass", () => {
  it("maps API rating strings to tone slugs", () => {
    expect(laneRatingChipToneClass(chip({ finalRating: "STRONG BUY" }))).toBe(
      "strong-buy",
    );
    expect(laneRatingChipToneClass(chip({ finalRating: "buy" }))).toBe("buy");
    expect(laneRatingChipToneClass(chip({ finalRating: "HOLD" }))).toBe(
      "hold",
    );
    expect(laneRatingChipToneClass(chip({ finalRating: "SELL" }))).toBe(
      "sell",
    );
    expect(
      laneRatingChipToneClass(chip({ finalRating: "STRONG SELL" })),
    ).toBe("strong-sell");
  });

  it("returns pending when finalRating is null", () => {
    expect(laneRatingChipToneClass(chip({ finalRating: null }))).toBe(
      "pending",
    );
  });

  it("returns unknown for unexpected rating text", () => {
    expect(laneRatingChipToneClass(chip({ finalRating: "N/A" }))).toBe(
      "unknown",
    );
  });
});

describe("laneRatingChipClassNames", () => {
  it("appends sentinel modifier for sentinel_rejection with a rating", () => {
    expect(
      laneRatingChipClassNames(
        chip({
          finalRating: "SELL",
          decisionType: "sentinel_rejection",
        }),
      ),
    ).toBe("lane-rating-chip lane-rating-chip--sell lane-rating-chip--sentinel");
  });

  it("omits sentinel modifier when arbiter", () => {
    expect(
      laneRatingChipClassNames(
        chip({ finalRating: "BUY", decisionType: "arbiter" }),
      ),
    ).toBe("lane-rating-chip lane-rating-chip--buy");
  });
});

describe("recommendationRatingClassNames", () => {
  it("builds table cell classes with optional sentinel marker", () => {
    expect(recommendationRatingClassNames("HOLD", "arbiter")).toBe(
      "recommendations-rating recommendations-rating--hold",
    );
    expect(
      recommendationRatingClassNames("SELL", "sentinel_rejection"),
    ).toBe(
      "recommendations-rating recommendations-rating--sell recommendations-rating--sentinel",
    );
  });
});
