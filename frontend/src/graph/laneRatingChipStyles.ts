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

/** Rating cell in the recommendations table. */
export function recommendationRatingClassNames(finalRating: string | null): string {
  const tone = finalRatingToneSlug(finalRating);
  return `recommendations-rating recommendations-rating--${tone}`;
}
