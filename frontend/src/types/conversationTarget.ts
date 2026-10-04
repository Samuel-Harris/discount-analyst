import type { AgentNameSlug, WorkflowScopedAgentNameSlug } from "@/api";

export type ConversationTarget =
  | {
      kind: "workflow_agent";
      workflowRunId: string;
      agentName: WorkflowScopedAgentNameSlug;
    }
  | { kind: "run_agent"; runId: string; agentName: AgentNameSlug };
