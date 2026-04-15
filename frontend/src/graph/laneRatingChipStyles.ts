import type { LaneRatingChipLayout } from "./buildGraphLayout";

type DecisionType = LaneRatingChipLayout["decisionType"];

/** CSS tone slug from `final_rating` (matches API `InvestmentRating` strings). */
export function finalRatingToneSlug(finalRating: string | null): string {
  if (!finalRating) return "pending";
  switch (finalRating.toUpperCase()) {
    case "STRONG BUY":
      return "strong-buy";
    case "BUY":
      return "buy";
    case "HOLD":
      return "hold";
    case "SELL":
      return "sell";
    case "STRONG SELL":
      return "strong-sell";
    default:
      return "unknown";
  }
}

/** CSS suffix for `lane-rating-chip--*` (matches API `InvestmentRating` strings). */
export function laneRatingChipToneClass(chip: LaneRatingChipLayout): string {
  return finalRatingToneSlug(chip.finalRating);
}

/** Rating cell in the recommendations table (shares tone colours with lane chips). */
export function recommendationRatingClassNames(
  finalRating: string | null,
  decisionType: DecisionType,
): string {
  const tone = finalRatingToneSlug(finalRating);
  const sentinel =
    decisionType === "sentinel_rejection" && finalRating
      ? " recommendations-rating--sentinel"
      : "";
  return `recommendations-rating recommendations-rating--${tone}${sentinel}`;
}

export function laneRatingChipClassNames(chip: LaneRatingChipLayout): string {
  const tone = laneRatingChipToneClass(chip);
  const sentinel =
    chip.decisionType === "sentinel_rejection" && chip.finalRating
      ? " lane-rating-chip--sentinel"
      : "";
  return `lane-rating-chip lane-rating-chip--${tone}${sentinel}`;
}
