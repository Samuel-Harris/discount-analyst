import { render, screen, waitFor } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as api from "@/api";
import * as serverState from "@/lib/server-state/invalidation";
import { RunPipelineForm } from "./RunPipelineForm";

const emptyPortfolio = {
  positions: [],
  cash_gbp: 0,
  suggestion_tickers: [],
};

async function expandLaunch(user: UserEvent) {
  await user.click(
    await screen.findByRole("button", { name: /expand launch panel/i }),
  );
}

describe("RunPipelineForm", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("starts collapsed and expands to the form", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "fetchPortfolio").mockResolvedValue(emptyPortfolio);
    vi.spyOn(serverState, "invalidateWorkflowRunsList").mockResolvedValue();
    render(<RunPipelineForm onLaunched={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: /expand launch panel/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Position ticker 1"),
    ).not.toBeInTheDocument();
    await expandLaunch(user);
    expect(
      screen.getByRole("heading", { name: "Launch workflow" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Position ticker 1")).toBeInTheDocument();
    await user.click(
      screen.getByRole("button", { name: "Collapse launch panel" }),
    );
    expect(
      screen.queryByLabelText("Position ticker 1"),
    ).not.toBeInTheDocument();
  });

  it("hides the rail when hidden is set", () => {
    vi.spyOn(api, "fetchPortfolio").mockResolvedValue(emptyPortfolio);
    vi.spyOn(serverState, "invalidateWorkflowRunsList").mockResolvedValue();
    const { container } = render(
      <RunPipelineForm onLaunched={vi.fn()} hidden />,
    );
    expect(
      screen.queryByRole("button", { name: /expand launch panel/i }),
    ).not.toBeInTheDocument();
    const rail = container.querySelector(".launch-rail");
    expect(rail).toHaveAttribute("hidden");
    expect(rail).not.toBeVisible();
  });

  it("prefills holdings, cash, and also-analyse pills from GET /api/portfolio", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "fetchPortfolio").mockResolvedValue({
      positions: [
        { ticker: "CBOX.L", value_gbp: 1500 },
        { ticker: "VTVI", value_gbp: 500 },
      ],
      cash_gbp: 200,
      suggestion_tickers: ["HINT.L"],
    });
    vi.spyOn(api, "createWorkflowRun").mockResolvedValue({
      workflow_run_id: "wf-1",
      profiler_runs: [],
      surveyor_started: true,
    });
    vi.spyOn(serverState, "invalidateWorkflowRunsList").mockResolvedValue();
    render(<RunPipelineForm onLaunched={vi.fn()} />);
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /expand launch panel/i }),
      ).toHaveAccessibleName(/2 holdings · £2,200\.00 · 1 extra/i);
    });
    await expandLaunch(user);
    expect(screen.getByLabelText("Position ticker 1")).toHaveValue("CBOX.L");
    expect(screen.getByLabelText("Position value in pounds 1")).toHaveValue(
      1500,
    );
    expect(screen.getByLabelText("Position ticker 2")).toHaveValue("VTVI");
    expect(screen.getByLabelText("Cash in pounds")).toHaveValue(200);
    expect(screen.getByText("HINT.L")).toBeInTheDocument();
  });

  it("defaults to mock mode and labels the slower simulated path", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "fetchPortfolio").mockResolvedValue(emptyPortfolio);
    vi.spyOn(serverState, "invalidateWorkflowRunsList").mockResolvedValue();
    render(<RunPipelineForm onLaunched={vi.fn()} />);
    await expandLaunch(user);
    const mockBox = screen.getByRole("checkbox", { name: /mock mode/i });
    expect(mockBox).toBeChecked();
    expect(mockBox).toBeDisabled();
    expect(
      screen.getByText(
        /mock mode \(required in dev; no live llm; slower simulated steps\)/i,
      ),
    ).toBeInTheDocument();
  });

  it("turns an also-analyse ticker into a pill when Enter is pressed", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "fetchPortfolio").mockResolvedValue(emptyPortfolio);
    vi.spyOn(serverState, "invalidateWorkflowRunsList").mockResolvedValue();
    render(<RunPipelineForm onLaunched={vi.fn()} />);
    await expandLaunch(user);
    const field = screen.getByLabelText("Also analyse");
    await user.type(field, "AAA.L{Enter}");
    expect(screen.getByText("AAA.L")).toBeInTheDocument();
    expect(field).toHaveValue("");
  });

  it("submits positions, cash_gbp, suggestion_tickers, and is_mock", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "fetchPortfolio").mockResolvedValue(emptyPortfolio);
    const create = vi.spyOn(api, "createWorkflowRun").mockResolvedValue({
      workflow_run_id: "wf-new",
      profiler_runs: [{ run_id: "r1", ticker: "AAA.L" }],
      surveyor_started: true,
    });
    const onLaunched = vi.fn();
    const invalidate = vi
      .spyOn(serverState, "invalidateWorkflowRunsList")
      .mockResolvedValue();
    render(<RunPipelineForm onLaunched={onLaunched} />);
    await expandLaunch(user);
    await screen.findByLabelText("Also analyse");
    await user.type(screen.getByLabelText("Position ticker 1"), "AAA.L");
    await user.type(
      screen.getByLabelText("Position value in pounds 1"),
      "2500",
    );
    await user.clear(screen.getByLabelText("Cash in pounds"));
    await user.type(screen.getByLabelText("Cash in pounds"), "500");
    await user.type(screen.getByLabelText("Also analyse"), "HINT.L");
    await user.click(screen.getByRole("button", { name: /start workflow/i }));
    await waitFor(() => {
      expect(create).toHaveBeenCalledWith({
        positions: [{ ticker: "AAA.L", value_gbp: 2500 }],
        cash_gbp: 500,
        suggestion_tickers: ["HINT.L"],
        is_mock: true,
      });
    });
    expect(onLaunched).toHaveBeenCalledWith("wf-new");
    expect(invalidate).toHaveBeenCalledTimes(1);
  });

  it("disables controls while a launch is in flight", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "fetchPortfolio").mockResolvedValue(emptyPortfolio);
    let release!: () => void;
    const barrier = new Promise<void>((resolve) => {
      release = resolve;
    });
    vi.spyOn(api, "createWorkflowRun").mockImplementation(async () => {
      await barrier;
      return {
        workflow_run_id: "wf-slow",
        profiler_runs: [],
        surveyor_started: true,
      };
    });
    vi.spyOn(serverState, "invalidateWorkflowRunsList").mockResolvedValue();
    render(<RunPipelineForm onLaunched={vi.fn()} />);
    await expandLaunch(user);
    await screen.findByLabelText("Also analyse");
    await user.type(screen.getByLabelText("Also analyse"), "Z.L");
    const submit = screen.getByRole("button", { name: /start workflow/i });
    await user.click(submit);
    await waitFor(() => {
      expect(screen.getByLabelText("Also analyse")).toBeDisabled();
    });
    expect(screen.getByRole("checkbox", { name: /mock mode/i })).toBeDisabled();
    release();
    await waitFor(() => {
      expect(screen.getByLabelText("Also analyse")).not.toBeDisabled();
    });
  });
});
