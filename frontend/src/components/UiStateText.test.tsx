import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { UiStateText } from "./UiStateText";

describe("UiStateText", () => {
  it("applies tone classes for loading and error", () => {
    const { rerender } = render(
      <UiStateText tone="loading" as="p">
        Please wait
      </UiStateText>,
    );
    const p = screen.getByText("Please wait");
    expect(p).toHaveClass("ui-state-text", "ui-state-text--loading");

    rerender(
      <UiStateText tone="error" as="p">
        Failed
      </UiStateText>,
    );
    expect(screen.getByText("Failed")).toHaveClass("ui-state-text--error");
  });
});
