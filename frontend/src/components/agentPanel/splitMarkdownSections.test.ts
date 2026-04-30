import { describe, expect, it } from "vitest";

import { splitMarkdownSections } from "./splitMarkdownSections";

describe("splitMarkdownSections", () => {
  it("treats a document with no depth-1/2 split lines as a single section", () => {
    const doc = "## Only top section\n\nBody here.";
    const sections = splitMarkdownSections(doc);
    expect(sections).toHaveLength(1);
    expect(sections[0].summaryLabel).toBe("Only top section");
    expect(sections[0].body).toBe(doc);
  });

  it("uses Introduction for a preamble before the first heading", () => {
    const doc = "Intro line\n\n# First\n\nUnder first.";
    const sections = splitMarkdownSections(doc);
    expect(sections).toHaveLength(2);
    expect(sections[0].summaryLabel).toBe("Introduction");
    expect(sections[0].body).toContain("Intro line");
    expect(sections[1].summaryLabel).toBe("First");
    expect(sections[1].body).toMatch(/^# First/m);
  });

  it("splits on both # and ## at line starts", () => {
    const doc = "# One\n\nA\n## Two\n\nB";
    const sections = splitMarkdownSections(doc);
    expect(sections).toHaveLength(2);
    expect(sections[0].summaryLabel).toBe("One");
    expect(sections[1].summaryLabel).toBe("Two");
  });

  it("does not split on # inside fenced code blocks", () => {
    const doc = [
      "Before",
      "```",
      "# not a heading",
      "## also not",
      "```",
      "",
      "## Real",
      "text",
    ].join("\n");
    const sections = splitMarkdownSections(doc);
    expect(sections).toHaveLength(2);
    expect(sections[0].summaryLabel).toBe("Introduction");
    expect(sections[0].body).toContain("# not a heading");
    expect(sections[1].summaryLabel).toBe("Real");
  });
});
