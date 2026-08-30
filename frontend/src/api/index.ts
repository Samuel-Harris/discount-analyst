import {
  getWorkflowAgentConversationApiAgentsWorkflowRunsWorkflowRunIdAgentsWorkflowAgentNameConversationGet,
  type ConversationResponse,
} from "./generated";

export type {
  AgentExecutionSummary,
  ConversationResponse,
  CreateWorkflowRunRequest,
  CreateWorkflowRunResponse,
  DashboardStatusResponse,
  EntryPathApi,
  ExecutionStatusApi,
  PortfolioResponse,
  TickerRunDetail,
  WorkflowRunDetailResponse,
  WorkflowRunListItem,
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

export function fetchSurveyorConversation(
  workflowRunId: string,
  options?: RequestInit,
): Promise<ConversationResponse> {
  return getWorkflowAgentConversationApiAgentsWorkflowRunsWorkflowRunIdAgentsWorkflowAgentNameConversationGet(
    workflowRunId,
    "surveyor",
    options,
  );
}
