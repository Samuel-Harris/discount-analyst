import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as api from "../api";
import * as serverState from "../serverState";
import { RunPipelineForm } from "./RunPipelineForm";

describe("RunPipelineForm", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("prefills tickers from GET /api/portfolio when none set yet", async () => {
    vi.spyOn(api, "fetchPortfolio").mockResolvedValue({
      portfolio_tickers: ["CBOX.L", "VTVI"],
    });
    vi.spyOn(api, "createWorkflowRun").mockResolvedValue({
      workflow_run_id: "wf-1",
      profiler_runs: [],
      surveyor_started: true,
    });
    const onLaunched = vi.fn();
    vi.spyOn(serverState, "invalidateWorkflowRunsList").mockResolvedValue();
    render(<RunPipelineForm onLaunched={onLaunched} />);
    await waitFor(() => {
      expect(screen.getByText("CBOX.L")).toBeInTheDocument();
      expect(screen.getByText("VTVI")).toBeInTheDocument();
    });
  });

  it("defaults to mock mode and labels the slower simulated path", () => {
    vi.spyOn(api, "fetchPortfolio").mockResolvedValue({
      portfolio_tickers: [],
    });
    vi.spyOn(serverState, "invalidateWorkflowRunsList").mockResolvedValue();
    render(<RunPipelineForm onLaunched={vi.fn()} />);
    const mockBox = screen.getByRole("checkbox", { name: /mock mode/i });
    expect(mockBox).toBeChecked();
    expect(mockBox).toBeDisabled();
    expect(
      screen.getByText(
        /mock mode \(required in dev; no live llm; slower simulated steps\)/i,
      ),
    ).toBeInTheDocument();
  });

  it("turns a ticker into a pill when Enter is pressed", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "fetchPortfolio").mockResolvedValue({
      portfolio_tickers: [],
    });
    vi.spyOn(serverState, "invalidateWorkflowRunsList").mockResolvedValue();
    render(<RunPipelineForm onLaunched={vi.fn()} />);
    const field = screen.getByLabelText("Portfolio tickers");
    await user.type(field, "AAA.L{Enter}");
    expect(screen.getByText("AAA.L")).toBeInTheDocument();
    expect(field).toHaveValue("");
  });

  it("submits portfolio_tickers and is_mock matching the create contract", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "fetchPortfolio").mockResolvedValue({
      portfolio_tickers: [],
    });
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
    await screen.findByLabelText("Portfolio tickers");
    await user.type(screen.getByLabelText("Portfolio tickers"), "AAA.L");
    await user.click(screen.getByRole("button", { name: /start workflow/i }));
    await waitFor(() => {
      expect(create).toHaveBeenCalledWith({
        portfolio_tickers: ["AAA.L"],
        is_mock: true,
      });
    });
    expect(onLaunched).toHaveBeenCalledWith("wf-new");
    expect(invalidate).toHaveBeenCalledTimes(1);
  });

  it("disables controls while a launch is in flight", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "fetchPortfolio").mockResolvedValue({
      portfolio_tickers: [],
    });
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
    await screen.findByLabelText("Portfolio tickers");
    await user.type(screen.getByLabelText("Portfolio tickers"), "Z.L");
    const submit = screen.getByRole("button", { name: /start workflow/i });
    await user.click(submit);
    await waitFor(() => {
      expect(screen.getByLabelText("Portfolio tickers")).toBeDisabled();
    });
    expect(screen.getByRole("checkbox", { name: /mock mode/i })).toBeDisabled();
    release();
    await waitFor(() => {
      expect(screen.getByLabelText("Portfolio tickers")).not.toBeDisabled();
    });
  });
});
