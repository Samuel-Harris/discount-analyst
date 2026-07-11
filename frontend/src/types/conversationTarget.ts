import type { AgentNameSlug } from "@/api";

export type ConversationTarget =
  | { kind: "surveyor"; workflowRunId: string }
  | { kind: "run_agent"; runId: string; agentName: AgentNameSlug };
