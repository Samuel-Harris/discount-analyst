import { useCallback, useState } from "react";

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

  const load = useCallback(async (target: ConversationTarget) => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res =
        target.kind === "surveyor"
          ? await fetchSurveyorConversation(target.workflowRunId)
          : await fetchRunAgentConversation(target.runId, target.agentName);
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Conversation unavailable");
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, load, clear };
}
