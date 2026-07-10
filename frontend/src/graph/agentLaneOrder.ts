import type { AgentNameSlug } from "../api";

/** Matches ``backend.contracts.agent_lane_order.PROFILER_ENTRY_AGENT_NAMES``. */
export const PROFILER_ENTRY_AGENT_NAMES = [
  "profiler",
  "researcher",
  "strategist",
  "sentinel",
  "appraiser",
] as const satisfies readonly AgentNameSlug[];

/** Matches ``backend.contracts.agent_lane_order.SURVEYOR_ENTRY_AGENT_NAMES``. */
export const SURVEYOR_ENTRY_AGENT_NAMES = [
  "researcher",
  "strategist",
  "sentinel",
  "appraiser",
] as const satisfies readonly AgentNameSlug[];

/** Agent slugs that may appear on any ticker lane (profiler- or surveyor-entry). */
export const LANE_AGENT_SLUGS = new Set<string>(PROFILER_ENTRY_AGENT_NAMES);

/** Column / chain ordering for profiler-entry lanes in ``buildGraphLayout``. */
export const GRAPH_LAYOUT_PROFILER_LANE_ORDER: readonly AgentNameSlug[] =
  PROFILER_ENTRY_AGENT_NAMES;
