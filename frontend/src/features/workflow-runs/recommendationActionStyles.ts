import type { RebalanceAction } from "@/api";

/** Action cell in the Curator book positions table. */
export function recommendationActionClassNames(action: RebalanceAction): string {
  switch (action) {
    case "enter":
    case "increase":
    case "hold":
    case "reduce":
    case "exit":
    case "avoid":
      return `recommendations-action recommendations-action--${action}`;
    default: {
      const unhandled: never = action;
      void unhandled;
      return "recommendations-action recommendations-action--unknown";
    }
  }
}
