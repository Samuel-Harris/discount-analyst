"""Persistence and orchestration ports for dashboard pipeline stages."""

from __future__ import annotations

from typing import Any, Protocol


class ProfilerStagePort(Protocol):
    """Narrow interface used by the profiler pipeline stage (DB + status hooks)."""

    async def get_agent_execution_id(self, run_id: str, agent_name: str) -> str | None:
        """Resolve the agent execution row id for a ticker run and agent name."""

    async def mark_agent_execution(
        self,
        *,
        execution_id: str,
        status: str,
        output_json: str | None = None,
        started: bool = False,
        completed: bool = False,
        error_message: str | None = None,
    ) -> None:
        """Update agent execution status, timestamps, output, or error."""

    async def recompute_workflow_status(self, workflow_run_id: str) -> None:
        """Refresh derived workflow status after a stage transition."""

    async def store_agent_conversation(
        self,
        *,
        run_id: str,
        agent_name: str,
        system_prompt: str,
        messages: list[Any] | None = None,
        messages_json: str | None = None,
    ) -> None:
        """Persist streamed (or mock) conversation for an agent execution."""

    async def update_ticker_run_company_name(
        self, run_id: str, company_name: str
    ) -> None:
        """Update the display company name on the ticker run after profiler output."""
