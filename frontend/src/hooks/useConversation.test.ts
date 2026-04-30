import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ConversationResponse } from "../api";
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
    expect(surveyor).toHaveBeenCalledWith(
      "wf-1",
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
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
    expect(runAgent).toHaveBeenCalledWith(
      "run-1",
      "researcher",
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
    expect(surveyor).not.toHaveBeenCalled();
    expect(result.current.data).toEqual(payload);
  });

  it("keeps only the latest conversation when load is called again before the prior request finishes", async () => {
    let resolveSlow: (value: ConversationResponse) => void;
    const slow = new Promise<ConversationResponse>((resolve) => {
      resolveSlow = resolve;
    });
    const payloadA = {
      system_prompt: "a",
      messages_json: "[]",
      assistant_response: "{}",
    };
    const payloadB = {
      system_prompt: "b",
      messages_json: "[]",
      assistant_response: "{}",
    };
    vi.spyOn(api, "fetchSurveyorConversation").mockImplementation(() => slow);
    const runAgent = vi
      .spyOn(api, "fetchRunAgentConversation")
      .mockResolvedValue(payloadB);
    const { result } = renderHook(() => useConversation());
    await act(async () => {
      void result.current.load({
        kind: "surveyor",
        workflowRunId: "wf-slow",
      });
    });
    await act(async () => {
      await result.current.load({
        kind: "run_agent",
        runId: "run-fast",
        agentName: "researcher",
      });
    });
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(runAgent).toHaveBeenCalledWith(
      "run-fast",
      "researcher",
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
    expect(result.current.data).toEqual(payloadB);
    await act(async () => {
      resolveSlow!(payloadA);
      await Promise.resolve();
    });
    expect(result.current.data).toEqual(payloadB);
  });

  it("does not record an error when the in-flight request is superseded (abort)", async () => {
    const payload = {
      system_prompt: "ok",
      messages_json: "[]",
      assistant_response: "{}",
    };
    vi.spyOn(api, "fetchSurveyorConversation")
      .mockImplementationOnce((_id, init) => {
        return new Promise((_resolve, reject) => {
          init?.signal?.addEventListener(
            "abort",
            () => reject(new DOMException("Aborted", "AbortError")),
            { once: true },
          );
        });
      })
      .mockResolvedValueOnce(payload);
    const { result } = renderHook(() => useConversation());
    await act(async () => {
      void result.current.load({ kind: "surveyor", workflowRunId: "wf-1" });
    });
    await act(async () => {
      await result.current.load({ kind: "surveyor", workflowRunId: "wf-2" });
    });
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toBeNull();
    expect(result.current.data).toEqual(payload);
  });
});
