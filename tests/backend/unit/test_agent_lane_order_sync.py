"""Ensure dashboard lane agent ordering matches the frontend graph module."""

from __future__ import annotations

import re
from pathlib import Path

from backend.contracts.agent_lane_order import (
    PROFILER_ENTRY_AGENT_NAMES,
    SURVEYOR_ENTRY_AGENT_NAMES,
)


def _extract_ts_const_array(ts_text: str, const_name: str) -> tuple[str, ...]:
    pattern = rf"export const {re.escape(const_name)}\s*=\s*\[([\s\S]*?)\]\s+as const"
    match = re.search(pattern, ts_text)
    assert match is not None, f"could not find {const_name} in agentLaneOrder.ts"
    slugs = tuple(re.findall(r'"([a-z_]+)"', match.group(1)))
    assert slugs, f"{const_name} parsed to empty sequence"
    return slugs


def test_typescript_agent_lane_order_matches_backend_contract() -> None:
    ts_path = (
        Path(__file__).resolve().parents[3] / "frontend/src/graph/agentLaneOrder.ts"
    )
    text = ts_path.read_text(encoding="utf-8")
    assert _extract_ts_const_array(text, "PROFILER_ENTRY_AGENT_NAMES") == (
        PROFILER_ENTRY_AGENT_NAMES
    )
    assert _extract_ts_const_array(text, "SURVEYOR_ENTRY_AGENT_NAMES") == (
        SURVEYOR_ENTRY_AGENT_NAMES
    )
