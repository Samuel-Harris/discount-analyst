import { describe, expect, it } from "vitest";

import {
  finalRatingToneSlug,
  recommendationRatingClassNames,
} from "./laneRatingChipStyles";

describe("finalRatingToneSlug", () => {
  it("maps API rating strings to tone slugs", () => {
    expect(finalRatingToneSlug("STRONG BUY")).toBe("strong-buy");
    expect(finalRatingToneSlug("buy")).toBe("buy");
    expect(finalRatingToneSlug("HOLD")).toBe("hold");
    expect(finalRatingToneSlug("SELL")).toBe("sell");
    expect(finalRatingToneSlug("STRONG SELL")).toBe("strong-sell");
  });

  it("returns pending when finalRating is null", () => {
    expect(finalRatingToneSlug(null)).toBe("pending");
  });

  it("returns unknown for unexpected rating text", () => {
    expect(finalRatingToneSlug("N/A")).toBe("unknown");
  });
});

describe("recommendationRatingClassNames", () => {
  it("builds table cell classes from rating tone only", () => {
    expect(recommendationRatingClassNames("HOLD")).toBe(
      "recommendations-rating recommendations-rating--hold",
    );
    expect(recommendationRatingClassNames("SELL")).toBe(
      "recommendations-rating recommendations-rating--sell",
    );
  });
});
