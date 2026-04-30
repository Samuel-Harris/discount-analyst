"""Per-lane agent ordering for dashboard persistence and the workflow graph UI.

Ticker runs created with ``entry_path="profiler"`` use ``PROFILER_ENTRY_AGENT_NAMES``.
Surveyor-discovered lanes use ``SURVEYOR_ENTRY_AGENT_NAMES`` (no profiler execution).

The graph column order for profiler-entry lanes matches ``PROFILER_ENTRY_AGENT_NAMES``;
the dashboard frontend mirrors these tuples in ``frontend/src/graph/agentLaneOrder.ts``.
``tests/backend/unit/test_agent_lane_order_sync.py`` asserts both stay aligned.
"""

from typing import Final

PROFILER_ENTRY_AGENT_NAMES: Final[tuple[str, ...]] = (
    "profiler",
    "researcher",
    "strategist",
    "sentinel",
    "appraiser",
    "arbiter",
)

SURVEYOR_ENTRY_AGENT_NAMES: Final[tuple[str, ...]] = (
    "researcher",
    "strategist",
    "sentinel",
    "appraiser",
    "arbiter",
)
