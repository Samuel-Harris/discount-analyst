import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConversationMessagesList } from "./ConversationMessagesList";

describe("ConversationMessagesList", () => {
  it("shows per-turn input tokens and percent of the context window", () => {
    render(
      <ConversationMessagesList
        messagesJson={JSON.stringify([
          {
            kind: "request",
            parts: [{ part_kind: "user-prompt", content: "Analyse" }],
          },
          {
            kind: "response",
            parts: [{ part_kind: "text", content: "Done" }],
            usage: {
              input_tokens: 105000,
              context_window_tokens: 1050000,
              context_window_used_pct: 10,
            },
          },
        ])}
      />,
    );

    expect(screen.queryByText(/Context/)).not.toBeNull();
    expect(
      screen.getByText("Context 105,000 / 1,050,000 tokens (10.0%)"),
    ).toBeInTheDocument();
  });

  it("omits context usage when a historical message has none", () => {
    render(
      <ConversationMessagesList
        messagesJson={JSON.stringify([
          {
            kind: "response",
            parts: [{ part_kind: "text", content: "Legacy" }],
          },
        ])}
      />,
    );

    expect(screen.getByText("Response")).toBeInTheDocument();
    expect(screen.queryByText(/Context/)).toBeNull();
  });
});
