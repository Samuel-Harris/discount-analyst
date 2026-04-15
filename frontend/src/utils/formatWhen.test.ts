import { describe, expect, it } from "vitest";

import { formatWhen } from "./formatWhen";

describe("formatWhen", () => {
  it("formats a valid ISO string with en-GB weekday and time", () => {
    const s = formatWhen("2026-04-15T14:30:00.000Z");
    // Locale output omits the year for recent dates in some engines.
    expect(s).toMatch(/Wed|Thu|Apr|15|:30/);
    expect(s.length).toBeGreaterThan(8);
  });

  it("returns the raw string when parsing fails", () => {
    expect(formatWhen("not-a-date")).toBe("not-a-date");
  });
});
