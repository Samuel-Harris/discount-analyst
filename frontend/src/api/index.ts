import {
  getWorkflowAgentConversationApiAgentsWorkflowRunsWorkflowRunIdAgentsWorkflowAgentNameConversationGet,
  getWorkflowAllocationApiWorkflowRunsWorkflowRunIdAllocationGet,
  type ConversationResponse,
  type PortfolioAllocation,
  type WorkflowScopedAgentNameSlug,
} from "./generated";
import { DashboardApiError } from "./orval-mutator";

export type {
  AgentExecutionSummary,
  AllocationPosition,
  CashAllocation,
  ConversationResponse,
  CreateWorkflowRunRequest,
  CreateWorkflowRunResponse,
  DashboardStatusResponse,
  EntryPathApi,
  ExecutionStatusApi,
  PortfolioAllocation,
  PortfolioPositionInput,
  PortfolioResponse,
  RebalanceAction,
  SharedRiskCluster,
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

export async function fetchWorkflowAllocation(
  workflowRunId: string,
  options?: RequestInit,
): Promise<PortfolioAllocation | null> {
  try {
    return await getWorkflowAllocationApiWorkflowRunsWorkflowRunIdAllocationGet(
      workflowRunId,
      options,
    );
  } catch (e) {
    if (e instanceof DashboardApiError && e.status === 404) return null;
    throw e;
  }
}
