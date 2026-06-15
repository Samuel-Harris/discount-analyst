"""Docker-backed terminal capability for pipeline agents (``terminal_exec``)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, cast
from uuid import uuid4

import httpx
from pydantic import BaseModel
from pydantic_ai import FunctionToolset
from pydantic_ai.capabilities.abstract import AbstractCapability
from pydantic_ai.toolsets import AgentToolset

from common.config import Settings
from discount_analyst.integrations.infallible_toolset import InfallibleToolset

logger = logging.getLogger(__name__)

_PROBE_SESSION_TIMEOUT_S = 120.0


class TerminalUnavailableError(RuntimeError):
    """Raised when the agent-terminal orchestrator cannot create a sandbox session."""

    def __init__(
        self,
        *,
        service_url: str,
        reason: str,
        detail: str | None = None,
    ) -> None:
        self.service_url = service_url
        self.reason = reason
        self.detail = detail
        parts = [f"Terminal unavailable at {service_url}: {reason}"]
        if detail:
            parts.append(detail)
        super().__init__("\n".join(parts))


def _http_error_detail(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip() or None
    if not isinstance(payload, dict):
        return response.text.strip() or None
    body = cast(dict[str, Any], payload)
    detail_value = body.get("detail")
    if isinstance(detail_value, str):
        return detail_value
    if detail_value is not None:
        return str(detail_value)
    return response.text.strip() or None


async def ensure_terminal_ready(
    *,
    service_url: str,
    probe_session_id: str | None = None,
) -> None:
    """Verify the orchestrator can create a sandbox before an agent run starts."""
    base = service_url.rstrip("/")
    session_id = probe_session_id or f"terminal-probe-{uuid4()}"
    try:
        async with httpx.AsyncClient(timeout=_PROBE_SESSION_TIMEOUT_S) as client:
            create_resp = await client.post(
                f"{base}/sessions",
                json={"session_id": session_id},
                timeout=_PROBE_SESSION_TIMEOUT_S,
            )
            if create_resp.is_error:
                detail = _http_error_detail(create_resp)
                raise TerminalUnavailableError(
                    service_url=service_url,
                    reason=(
                        f"session creation failed with HTTP {create_resp.status_code}"
                    ),
                    detail=detail,
                )
            delete_resp = await client.delete(f"{base}/sessions/{session_id}")
            if delete_resp.status_code not in (204, 404):
                logger.warning(
                    "Terminal probe session delete returned %s for session_id=%s: %s",
                    delete_resp.status_code,
                    session_id,
                    delete_resp.text[:500],
                )
    except httpx.HTTPStatusError as exc:
        detail = _http_error_detail(exc.response)
        raise TerminalUnavailableError(
            service_url=service_url,
            reason=f"session creation failed with HTTP {exc.response.status_code}",
            detail=detail,
        ) from exc
    except httpx.RequestError as exc:
        raise TerminalUnavailableError(
            service_url=service_url,
            reason=f"connection failed ({type(exc).__name__})",
            detail=str(exc),
        ) from exc


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
    """Per-run HTTP client and lazy orchestrator session create flag."""

    ready: bool = False
    client: httpx.AsyncClient | None = None


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


def _terminal_http_timeout(limits: TerminalLimits) -> httpx.Timeout:
    return httpx.Timeout(
        connect=30.0,
        read=float(limits.command_timeout_s) + 30.0,
        write=30.0,
        pool=30.0,
    )


async def _client_for_state(
    state: TerminalSessionState, limits: TerminalLimits
) -> httpx.AsyncClient:
    if state.client is None:
        state.client = httpx.AsyncClient(timeout=_terminal_http_timeout(limits))
    return state.client


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
    client = await _client_for_state(state, limits)
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


async def close_terminal_http(session_state: TerminalSessionState | None) -> None:
    """Close the per-run shared HTTP client, if one was opened."""
    if session_state is None or session_state.client is None:
        return
    await session_state.client.aclose()
    session_state.client = None


@dataclass
class Terminal(AbstractCapability[None]):
    """Registers an infallible ``terminal_exec`` toolset hitting the agent-terminal HTTP API."""

    service_url: str
    limits: TerminalLimits
    session_id: str
    session_state: TerminalSessionState = field(default_factory=TerminalSessionState)

    def get_toolset(self) -> AgentToolset[None] | None:
        service_url = self.service_url.rstrip("/")
        limits = self.limits
        session_id = self.session_id
        session_state = self.session_state

        async def terminal_exec(command: str) -> str:
            """Run a shell command in the per-run sandbox container.

            Args:
                command: Shell command string passed to ``/bin/sh -c``.

            Returns:
                Text block with exit code, stdout, stderr, and truncation note if applicable.
            """
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
