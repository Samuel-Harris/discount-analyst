import { describe, expect, it } from "vitest";

import {
  formatWorkflowRunUrlSearch,
  parseWorkflowRunUrlSearch,
} from "./useWorkflowRunNavigation";

describe("parseWorkflowRunUrlSearch", () => {
  it("reads run id and recommendations view", () => {
    expect(parseWorkflowRunUrlSearch("?run=wf-1&view=recommendations")).toEqual(
      {
        selectedId: "wf-1",
        mainView: "recommendations",
      },
    );
  });

  it("ignores recommendations view without a run id", () => {
    expect(parseWorkflowRunUrlSearch("?view=recommendations")).toEqual({
      selectedId: null,
      mainView: "pipeline",
    });
  });

  it("defaults to pipeline when only run is set", () => {
    expect(parseWorkflowRunUrlSearch("?run=abc")).toEqual({
      selectedId: "abc",
      mainView: "pipeline",
    });
  });
});

describe("formatWorkflowRunUrlSearch", () => {
  it("round-trips recommendations state", () => {
    const state = {
      selectedId: "wf-9",
      mainView: "recommendations" as const,
    };
    expect(parseWorkflowRunUrlSearch(formatWorkflowRunUrlSearch(state))).toEqual(
      state,
    );
  });

  it("returns empty string when no run selected", () => {
    expect(
      formatWorkflowRunUrlSearch({ selectedId: null, mainView: "pipeline" }),
    ).toBe("");
  });
});
