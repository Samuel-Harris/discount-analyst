import { useCallback, useRef, useState } from "react";

import {
  fetchRunAgentConversation,
  fetchWorkflowAgentConversation,
  type ConversationResponse,
} from "@/api";
import type { ConversationTarget } from "@/types/conversationTarget";

export function useConversation() {
  const [data, setData] = useState<ConversationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestSeqRef = useRef(0);
  const abortRef = useRef<AbortController | null>(null);

  const load = useCallback(async (target: ConversationTarget) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const mySeq = ++requestSeqRef.current;

    setLoading(true);
    setError(null);
    setData(null);
    try {
      const signal = controller.signal;
      let res: ConversationResponse;
      switch (target.kind) {
        case "workflow_agent":
          res = await fetchWorkflowAgentConversation(
            target.workflowRunId,
            target.agentName,
            { signal },
          );
          break;
        case "run_agent":
          res = await fetchRunAgentConversation(target.runId, target.agentName, {
            signal,
          });
          break;
        default: {
          const unhandled: never = target;
          throw new Error(`Unhandled conversation target: ${String(unhandled)}`);
        }
      }
      if (mySeq !== requestSeqRef.current) return;
      setData(res);
    } catch (e) {
      if (e instanceof Error && e.name === "AbortError") return;
      if (mySeq !== requestSeqRef.current) return;
      setError(e instanceof Error ? e.message : "Conversation unavailable");
    } finally {
      if (mySeq === requestSeqRef.current) setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    requestSeqRef.current += 1;
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, load, clear };
}
