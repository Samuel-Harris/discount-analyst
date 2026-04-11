import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Sidebar } from "./Sidebar";
import type { WorkflowRunListItem } from "../api";

const sample = (
  overrides: Partial<WorkflowRunListItem>,
): WorkflowRunListItem => ({
  id: "wf-mock-1",
  started_at: "2026-04-01T12:00:00Z",
  completed_at: null,
  status: "running",
  is_mock: true,
  error_message: null,
  ticker_run_count: 2,
  completed_ticker_run_count: 1,
  failed_ticker_run_count: 0,
  ...overrides,
});

describe("Sidebar", () => {
  it("shows summary counts for each workflow row", () => {
    render(
      <Sidebar
        items={[sample({ ticker_run_count: 3, completed_ticker_run_count: 2 })]}
        selectedId={null}
        onSelect={vi.fn()}
        onDelete={vi.fn()}
        collapsed={false}
        onToggleCollapse={vi.fn()}
      />,
    );
    expect(screen.getByText(/runs 2\/3/)).toBeInTheDocument();
  });

  it("renders delete only for mock workflow runs", () => {
    render(
      <Sidebar
        items={[
          sample({ id: "mock", is_mock: true }),
          sample({ id: "real", is_mock: false }),
        ]}
        selectedId={null}
        onSelect={vi.fn()}
        onDelete={vi.fn()}
        collapsed={false}
        onToggleCollapse={vi.fn()}
      />,
    );
    const delButtons = screen.getAllByTitle("Delete mock workflow");
    expect(delButtons).toHaveLength(1);
  });

  it("invokes onDelete when del is clicked", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    render(
      <Sidebar
        items={[sample({ id: "wf-del", is_mock: true })]}
        selectedId={null}
        onSelect={vi.fn()}
        onDelete={onDelete}
        collapsed={false}
        onToggleCollapse={vi.fn()}
      />,
    );
    await user.click(screen.getByTitle("Delete mock workflow"));
    expect(onDelete).toHaveBeenCalledWith("wf-del");
  });
});
