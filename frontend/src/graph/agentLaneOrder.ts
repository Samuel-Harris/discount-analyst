import type { AgentNameSlug } from "../api";

/** Matches ``backend.contracts.agent_lane_order.PROFILER_ENTRY_AGENT_NAMES``. */
export const PROFILER_ENTRY_AGENT_NAMES = [
  "profiler",
  "researcher",
  "strategist",
  "sentinel",
  "appraiser",
  "arbiter",
] as const satisfies readonly AgentNameSlug[];

/** Matches ``backend.contracts.agent_lane_order.SURVEYOR_ENTRY_AGENT_NAMES``. */
export const SURVEYOR_ENTRY_AGENT_NAMES = [
  "researcher",
  "strategist",
  "sentinel",
  "appraiser",
  "arbiter",
] as const satisfies readonly AgentNameSlug[];

/** Column / chain ordering for profiler-entry lanes in ``buildGraphLayout``. */
export const GRAPH_LAYOUT_PROFILER_LANE_ORDER: readonly AgentNameSlug[] =
  PROFILER_ENTRY_AGENT_NAMES;
