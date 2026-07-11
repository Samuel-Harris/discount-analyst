import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { ConversationResponse } from "@/api";

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

const mockAppraiserConversation: ConversationResponse = {
  system_prompt: "Appraiser system prompt",
  messages_json: "[]",
  assistant_response: JSON.stringify({
    ticker: "ABC.L",
    company_name: "ABC plc",
    valuation_date: "2026-06-04",
    summary: "Scenario-weighted valuation.",
    valuation_distribution: {
      currency: "GBP",
      current_share_price: 3,
      expected_intrinsic_value: 3.8,
      p10_intrinsic_value: 2.6,
      p25_intrinsic_value: 3.1,
      p50_intrinsic_value: 3.6,
      p75_intrinsic_value: 4.2,
      p90_intrinsic_value: 5,
      distribution_method: "scenario_weighting",
      distribution_reasoning: "Weighted scenarios.",
    },
    methods: [
      {
        method: "scenario_weighting",
        role: "primary",
        value_per_share: 3.8,
        weight_pct: 70,
      },
      {
        method: "comparable_multiples",
        role: "cross_check",
        value_per_share: 3.5,
        weight_pct: 30,
      },
    ],
    data_quality: "Medium",
  }),
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

  it("renders structured Appraiser valuation when agentName is appraiser", () => {
    const { container } = render(
      <AgentPanel
        open
        title="appraiser · ABC.L"
        agentName="appraiser"
        loading={false}
        error={null}
        data={mockAppraiserConversation}
        onClose={() => undefined}
      />,
    );

    const panel = container.querySelector<HTMLDivElement>(
      ".appraiser-valuation-panel",
    );
    expect(panel).not.toBeNull();
    expect(within(panel!).getByText(/Margin of safety/)).toBeInTheDocument();
    expect(screen.getByText("Raw JSON")).toBeInTheDocument();
  });
});
