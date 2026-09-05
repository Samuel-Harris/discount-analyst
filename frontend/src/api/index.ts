import {
  getWorkflowAgentConversationApiAgentsWorkflowRunsWorkflowRunIdAgentsWorkflowAgentNameConversationGet,
  type ConversationResponse,
  type WorkflowScopedAgentNameSlug,
} from "./generated";

export type {
  AgentExecutionSummary,
  ConversationResponse,
  CreateWorkflowRunRequest,
  CreateWorkflowRunResponse,
  DashboardStatusResponse,
  EntryPathApi,
  ExecutionStatusApi,
  PortfolioPositionInput,
  PortfolioResponse,
  TickerRunDetail,
  WorkflowRunDetailResponse,
  WorkflowRunListItem,
  WorkflowScopedAgentNameSlug,
  YfinanceFreshnessResponse,
} from "./generated";

export {
  AgentNameSlug,
  cancelWorkflowRunApiWorkflowRunsWorkflowRunIdCancelPost as cancelWorkflowRun,
  createWorkflowRunApiWorkflowRunsPost as createWorkflowRun,
  deleteWorkflowRunApiWorkflowRunsWorkflowRunIdDelete as deleteWorkflowRun,
  getDashboardStatusApiStatusGet as fetchDashboardStatus,
  getPortfolioApiPortfolioGet as fetchPortfolio,
  getRunAgentConversationApiAgentsRunsRunIdAgentsAgentNameConversationGet as fetchRunAgentConversation,
  getWorkflowRunApiWorkflowRunsWorkflowRunIdGet as fetchWorkflowRunDetail,
  listWorkflowRunsApiWorkflowRunsGet as fetchWorkflowRuns,
  retryFailedAgentsApiWorkflowRunsWorkflowRunIdRetryFailedAgentsPost as retryFailedAgents,
} from "./generated";

export function fetchWorkflowAgentConversation(
  workflowRunId: string,
  agentName: WorkflowScopedAgentNameSlug,
  options?: RequestInit,
): Promise<ConversationResponse> {
  return getWorkflowAgentConversationApiAgentsWorkflowRunsWorkflowRunIdAgentsWorkflowAgentNameConversationGet(
    workflowRunId,
    agentName,
    options,
  );
}
