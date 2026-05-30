"""Docker-backed terminal capability for pipeline agents (``terminal_exec``)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import BaseModel
from pydantic_ai import FunctionToolset
from pydantic_ai.capabilities.abstract import AbstractCapability
from pydantic_ai.toolsets import AgentToolset

from common.config import Settings
from discount_analyst.agents.common.terminal_context import get_terminal_session_id
from discount_analyst.integrations.infallible_toolset import InfallibleToolset

logger = logging.getLogger(__name__)

TERMINAL_EXEC_DESCRIPTION = """Run a shell command inside an isolated Linux sandbox for this agent run.

The sandbox persists for the whole run: files you create under ``/tmp`` or the working directory
remain visible to later ``terminal_exec`` calls until the run finishes.

Use for:
- Short Python or shell analysis (pandas, numpy, scipy, sympy, statsmodels, yfinance, etc.)
- Downloading or transforming tabular data when MCP is insufficient
- Sanity-checking arithmetic or small numerical experiments

Prefer project MCP and yfinance-backed tools when they already answer the question; use this
when you need arbitrary code execution.

Args:
    command: A shell command string passed to ``/bin/sh -c`` inside the sandbox.

Returns:
    A text block containing ``exit_code``, ``stdout``, ``stderr``, and whether output was truncated.
"""


@dataclass(frozen=True, slots=True)
class TerminalLimits:
    """Orchestrator-side limits mirrored in the client for UX and docstrings."""

    command_timeout_s: int
    max_output_bytes: int


@dataclass(frozen=True, slots=True)
class TerminalRuntimeConfig:
    """Explicit terminal HTTP settings (use when callers inject :class:`common.config.Settings`)."""

    service_url: str
    command_timeout_s: int
    max_output_bytes: int

    @classmethod
    def from_settings(cls, s: Settings) -> TerminalRuntimeConfig:
        return cls(
            service_url=s.terminal_service_url,
            command_timeout_s=s.terminal_command_timeout_s,
            max_output_bytes=s.terminal_max_output_bytes,
        )


@dataclass
class TerminalSessionState:
    """Per-toolset lazy session create flag (one orchestrator container per agent run)."""

    ready: bool = False


class TerminalExecPayload(BaseModel):
    """Orchestrator ``/exec`` JSON body."""

    exit_code: int
    stdout: str = ""
    stderr: str = ""
    truncated: bool = False


def format_terminal_exec_response(payload: TerminalExecPayload | dict[str, Any]) -> str:
    """Turn orchestrator JSON into the text block returned to the model."""
    parsed = (
        payload
        if isinstance(payload, TerminalExecPayload)
        else TerminalExecPayload.model_validate(payload)
    )
    exit_code = parsed.exit_code
    stdout = parsed.stdout
    stderr = parsed.stderr
    truncated = parsed.truncated
    note = (
        "\n(note: stdout/stderr were truncated to the configured byte cap)\n"
        if truncated
        else ""
    )
    return (
        f"exit_code: {exit_code}\n"
        f"{note}"
        "--- stdout ---\n"
        f"{stdout}\n"
        "--- stderr ---\n"
        f"{stderr}\n"
    )


async def execute_terminal_command(
    *,
    service_url: str,
    limits: TerminalLimits,
    session_id: str,
    command: str,
    session_state: TerminalSessionState | None = None,
) -> str:
    """POST session (once) then exec; used by the tool and unit tests."""
    base = service_url.rstrip("/")
    state = session_state or TerminalSessionState()
    timeout = httpx.Timeout(
        connect=30.0,
        read=float(limits.command_timeout_s) + 30.0,
        write=30.0,
        pool=30.0,
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        if not state.ready:
            resp = await client.post(
                f"{base}/sessions",
                json={"session_id": session_id},
                timeout=120.0,
            )
            resp.raise_for_status()
            state.ready = True
        exec_resp = await client.post(
            f"{base}/sessions/{session_id}/exec",
            json={"command": command},
        )
        exec_resp.raise_for_status()
        return format_terminal_exec_response(
            TerminalExecPayload.model_validate(exec_resp.json())
        )


@dataclass
class Terminal(AbstractCapability[None]):
    """Registers an infallible ``terminal_exec`` toolset hitting the agent-terminal HTTP API."""

    service_url: str
    limits: TerminalLimits

    def get_toolset(self) -> AgentToolset[None] | None:
        service_url = self.service_url.rstrip("/")
        limits = self.limits
        session_state = TerminalSessionState()

        async def terminal_exec(command: str) -> str:
            """Run a shell command in the per-run sandbox container.

            Args:
                command: Shell command string passed to ``/bin/sh -c``.

            Returns:
                Text block with exit code, stdout, stderr, and truncation note if applicable.
            """
            session_id = get_terminal_session_id()
            if not session_id:
                return (
                    "Tool 'terminal_exec' failed: no terminal session id is bound for this "
                    "agent run (internal configuration error). Try other tools or proceed "
                    "without sandbox execution."
                )
            return await execute_terminal_command(
                service_url=service_url,
                limits=limits,
                session_id=session_id,
                command=command,
                session_state=session_state,
            )

        toolset = FunctionToolset[None]()
        toolset.add_function(
            terminal_exec,
            name="terminal_exec",
            description=TERMINAL_EXEC_DESCRIPTION,
            docstring_format="google",
            require_parameter_descriptions=True,
        )
        return InfallibleToolset(toolset)


async def delete_terminal_session(service_url: str, session_id: str) -> None:
    """Best-effort ``DELETE /sessions/{id}``; logs warnings on failure."""
    base = service_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.delete(f"{base}/sessions/{session_id}")
            if resp.status_code not in (204, 404):
                logger.warning(
                    "Terminal session delete returned %s for session_id=%s: %s",
                    resp.status_code,
                    session_id,
                    resp.text[:500],
                )
    except Exception:
        logger.exception(
            "Terminal session delete failed for session_id=%s (orchestrator may leak until TTL sweep)",
            session_id,
        )
