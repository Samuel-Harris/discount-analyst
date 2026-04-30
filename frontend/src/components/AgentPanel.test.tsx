import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { ConversationResponse } from "../api";

import { AgentPanel } from "./AgentPanel";

const mockConversation: ConversationResponse = {
  system_prompt: [
    "# Role",
    "",
    "You are a test agent.",
    "",
    "## Rules",
    "",
    "- Be concise.",
  ].join("\n"),
  messages_json: JSON.stringify([
    {
      kind: "request",
      parts: [{ part_kind: "user-prompt", content: "Please **analyse**." }],
    },
    {
      kind: "response",
      parts: [
        {
          part_kind: "tool-call",
          tool_name: "lookup",
          args: JSON.stringify({ ticker: "ACME" }),
        },
      ],
    },
  ]),
  assistant_response: JSON.stringify({ verdict: "ok" }),
};

describe("AgentPanel", () => {
  it("renders conversation timeline chips and tool-call summary", () => {
    render(
      <AgentPanel
        open
        title="Surveyor"
        loading={false}
        error={null}
        data={mockConversation}
        onClose={() => undefined}
      />,
    );

    expect(screen.getByText("Request")).toBeInTheDocument();
    expect(screen.getByText("Response")).toBeInTheDocument();
    expect(screen.getByText("Message 1")).toBeInTheDocument();
    expect(screen.getByText("Message 2")).toBeInTheDocument();
    expect(screen.getByText(/lookup\(/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Rules/i })).toBeInTheDocument();
  });

  it("toggles system prompt between rendered sections and raw", async () => {
    const user = userEvent.setup();
    render(
      <AgentPanel
        open
        title="Surveyor"
        loading={false}
        error={null}
        data={mockConversation}
        onClose={() => undefined}
      />,
    );

    expect(screen.getByRole("button", { name: "Rendered" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(document.querySelector(".system-prompt-details")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Raw" }));
    expect(screen.getByRole("button", { name: "Raw" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(document.querySelector(".system-prompt-raw")).toBeTruthy();
    expect(document.querySelector(".system-prompt-details")).toBeNull();

    await user.click(screen.getByRole("button", { name: "Rendered" }));
    expect(document.querySelector(".system-prompt-details")).toBeTruthy();
  });
});
