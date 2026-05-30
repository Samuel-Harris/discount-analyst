"""Per-run terminal sandbox configuration (tool registration + session lifecycle)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import uuid4

from discount_analyst.integrations.terminal import TerminalRuntimeConfig

if TYPE_CHECKING:
    from common.config import Settings


@dataclass(frozen=True, slots=True)
class TerminalRunOptions:
    """Unified terminal flags for ``create_agent`` and ``run_streamed_agent``."""

    enabled: bool
    runtime: TerminalRuntimeConfig
    session_id: str | None = None

    def resolved_session_id(self) -> str:
        """Session id for the orchestrator, generating one when not preset."""
        return self.session_id or str(uuid4())


def terminal_run_options(
    settings: Settings,
    *,
    enabled: bool | None = None,
    session_id: str | None = None,
    runtime: TerminalRuntimeConfig | None = None,
) -> TerminalRunOptions:
    """Build terminal options from injected settings (dashboard, tests, scripts)."""
    effective_enabled = settings.use_terminal if enabled is None else enabled
    return TerminalRunOptions(
        enabled=effective_enabled,
        runtime=runtime or TerminalRuntimeConfig.from_settings(settings),
        session_id=session_id,
    )


def default_terminal_for_agent(
    settings: Settings,
    *,
    terminal: TerminalRunOptions | None,
) -> TerminalRunOptions:
    """Resolve terminal options for ``create_agent`` when the caller omits them."""
    if terminal is not None:
        return terminal
    return terminal_run_options(settings)
