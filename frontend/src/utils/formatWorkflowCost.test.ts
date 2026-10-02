import { describe, expect, it } from "vitest";

import { formatWorkflowCost } from "./formatWorkflowCost";

describe("formatWorkflowCost", () => {
  it("formats a priced amount in dollars to the stored two decimal places", () => {
    expect(
      formatWorkflowCost({ state: "amount", amount_usd: "12.30" }),
    ).toBe("$12.30");
  });

  it("shows unknown when the figure has no priced attempts", () => {
    expect(formatWorkflowCost({ state: "unknown", amount_usd: null })).toBe(
      "unknown",
    );
  });
});
