import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as api from "../api";
import { useConversation } from "./useConversation";

describe("useConversation", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loads surveyor conversation from the workflow-scoped endpoint", async () => {
    const payload = {
      system_prompt: "sys",
      messages_json: "[]",
      assistant_response: "{}",
    };
    const surveyor = vi
      .spyOn(api, "fetchSurveyorConversation")
      .mockResolvedValue(payload);
    const runAgent = vi.spyOn(api, "fetchRunAgentConversation");
    const { result } = renderHook(() => useConversation());
    await act(async () => {
      await result.current.load({ kind: "surveyor", workflowRunId: "wf-1" });
    });
    expect(result.current.loading).toBe(false);
    expect(surveyor).toHaveBeenCalledWith("wf-1");
    expect(runAgent).not.toHaveBeenCalled();
    expect(result.current.data).toEqual(payload);
    expect(result.current.error).toBeNull();
  });

  it("loads ticker agent conversation from the run-scoped endpoint", async () => {
    const payload = {
      system_prompt: "sys",
      messages_json: "[]",
      assistant_response: "{}",
    };
    const runAgent = vi
      .spyOn(api, "fetchRunAgentConversation")
      .mockResolvedValue(payload);
    const surveyor = vi.spyOn(api, "fetchSurveyorConversation");
    const { result } = renderHook(() => useConversation());
    await act(async () => {
      await result.current.load({
        kind: "run_agent",
        runId: "run-1",
        agentName: "researcher",
      });
    });
    expect(result.current.loading).toBe(false);
    expect(runAgent).toHaveBeenCalledWith("run-1", "researcher");
    expect(surveyor).not.toHaveBeenCalled();
    expect(result.current.data).toEqual(payload);
  });
});
