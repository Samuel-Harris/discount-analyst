import { describe, expect, it } from "vitest";

import type { RebalanceAction } from "@/api";
import { recommendationActionClassNames } from "./recommendationActionStyles";

const rebalanceActions: RebalanceAction[] = [
  "enter",
  "increase",
  "hold",
  "reduce",
  "exit",
  "avoid",
];

describe("recommendationActionClassNames", () => {
  it("builds table cell classes for each rebalance action", () => {
    for (const action of rebalanceActions) {
      expect(recommendationActionClassNames(action)).toBe(
        `recommendations-action recommendations-action--${action}`,
      );
    }
  });
});
