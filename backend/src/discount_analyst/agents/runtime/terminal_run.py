"""Per-run terminal sandbox configuration (tool registration + session lifecycle)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from pydantic_ai.agent.abstract import AbstractAgent
from pydantic_ai.usage import UsageLimits

from discount_analyst.agents.tools.terminal.client import (
    TerminalRuntimeConfig,
    TerminalSessionState,
)

if TYPE_CHECKING:
    from discount_analyst.config.settings import Settings

    from discount_analyst.agents.runtime.streamed_agent_run import (
        StreamedAgentRunOutcome,
    )


@dataclass(frozen=True, slots=True)
class TerminalRunOptions:
    """Unified terminal flags for ``create_agent`` and ``run_streamed_agent``."""

    enabled: bool
    runtime: TerminalRuntimeConfig
    session_id: str | None = None
    session_state: TerminalSessionState | None = None

    def bind_session_id(self) -> TerminalRunOptions:
        """Assign a stable ``session_id`` when not already preset."""
        if self.session_id is not None:
            return self
        return replace(self, session_id=str(uuid4()))

    def require_session_id(self) -> str:
        """Return ``session_id`` or raise when terminal is enabled but unbound."""
        if not self.enabled:
            msg = "require_session_id called on disabled terminal options"
            raise ValueError(msg)
        if self.session_id is None:
            msg = (
                "terminal.session_id is required when terminal is enabled; "
                "call bind_session_id() before create_agent"
            )
            raise ValueError(msg)
        return self.session_id


def terminal_run_options(
    settings: Settings,
    *,
    enabled: bool | None = None,
    session_id: str | None = None,
    runtime: TerminalRuntimeConfig | None = None,
) -> TerminalRunOptions:
    """Build terminal options from injected settings (dashboard, tests, scripts)."""
    effective_enabled = settings.use_terminal if enabled is None else enabled
    session_state = TerminalSessionState() if effective_enabled else None
    return TerminalRunOptions(
        enabled=effective_enabled,
        runtime=runtime or TerminalRuntimeConfig.from_settings(settings),
        session_id=session_id,
        session_state=session_state,
    )


async def run_agent_with_terminal[T](
    *,
    settings: Settings,
    session_id: str,
    build_agent: Callable[[TerminalRunOptions], AbstractAgent[Any, T]],
    user_prompt: str,
    usage_limits: UsageLimits,
    runtime: TerminalRuntimeConfig | None = None,
) -> StreamedAgentRunOutcome[T]:
    """Build terminal options, agent, and run with shared session lifecycle."""
    from discount_analyst.agents.runtime.streamed_agent_run import run_streamed_agent

    terminal = terminal_run_options(settings, session_id=session_id, runtime=runtime)
    if terminal.enabled:
        terminal = terminal.bind_session_id()
    agent = build_agent(terminal)
    return await run_streamed_agent(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=usage_limits,
        terminal=terminal,
        run_settings=settings,
    )
