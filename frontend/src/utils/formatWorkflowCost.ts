import {
  AgentNameSlug,
  type AgentTypeCost,
  type WorkflowCostFigure,
  type WorkflowRunDetailResponse,
} from "@/api";

export const ZERO_WORKFLOW_COST: WorkflowCostFigure = {
  state: "amount",
  amount_usd: "0.00",
};

export const ZERO_RUN_COST = {
  cost_total: ZERO_WORKFLOW_COST,
  cost_successful: ZERO_WORKFLOW_COST,
  cost_unsuccessful: ZERO_WORKFLOW_COST,
  cost_by_agent: Object.values(AgentNameSlug).map(
    (agent_name): AgentTypeCost => ({
      agent_name,
      cost: ZERO_WORKFLOW_COST,
    }),
  ),
} satisfies Pick<
  WorkflowRunDetailResponse,
  "cost_total" | "cost_successful" | "cost_unsuccessful" | "cost_by_agent"
>;

export function formatWorkflowCost(cost: WorkflowCostFigure): string {
  if (cost.state !== "amount" || cost.amount_usd == null) {
    return "unknown";
  }
  return `$${cost.amount_usd}`;
}
