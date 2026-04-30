import { useCallback, useRef, useState } from "react";

import {
  fetchRunAgentConversation,
  fetchSurveyorConversation,
  type AgentNameSlug,
  type ConversationResponse,
} from "../api";

export type ConversationTarget =
  | { kind: "surveyor"; workflowRunId: string }
  | { kind: "run_agent"; runId: string; agentName: AgentNameSlug };

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
      const res =
        target.kind === "surveyor"
          ? await fetchSurveyorConversation(target.workflowRunId, { signal })
          : await fetchRunAgentConversation(target.runId, target.agentName, {
              signal,
            });
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
