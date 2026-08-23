"""Wrapper toolset that catches tool exceptions and returns them as error messages.

When a tool fails (e.g., 402 Payment Required from FMP), instead of crashing the
agent run, this wrapper returns the error as a string result. The model can then
decide to try a different approach or report the limitation.

This is particularly useful for MCP tools where we don't control the error handling.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic_ai import (
    ApprovalRequired,
    CallDeferred,
    RunContext,
    SkipToolExecution,
)
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.toolsets.abstract import ToolsetTool
from pydantic_ai.toolsets.wrapper import WrapperToolset


class InfallibleToolset[AgentDepsT](WrapperToolset[AgentDepsT]):
    """Catches all tool exceptions and returns them as error messages.

    This allows the agent to continue when a tool fails, rather than crashing
    the entire run. The model receives an error message and can decide how
    to proceed (e.g., try a different tool, use cached data, or report the issue).
    """

    async def call_tool(
        self,
        name: str,
        tool_args: dict[str, Any],
        ctx: RunContext[AgentDepsT],
        tool: ToolsetTool[AgentDepsT],
    ) -> Any:
        try:
            return await super().call_tool(name, tool_args, ctx, tool)
        except Exception as exc:
            return format_tool_error(name, exc)


@dataclass
class InfallibleToolExecution[AgentDepsT](AbstractCapability[AgentDepsT]):
    """Convert non-output tool exceptions into ``format_tool_error`` strings.

    pydantic-ai re-raises ``ModelRetry`` before ``on_tool_execute_error``, so
    local ``web_fetch`` HTTP failures never reach that hook. This wraps execution
    instead. Output tools (``final_result``) still raise so structured-output
    repair stays intact.
    """

    async def wrap_tool_execute(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: dict[str, Any],
        handler: Callable[[dict[str, Any]], Awaitable[Any]],
    ) -> Any:
        del ctx, call
        try:
            return await handler(args)
        except (SkipToolExecution, CallDeferred, ApprovalRequired):
            raise
        except Exception as exc:
            if tool_def.kind == "output":
                raise
            return format_tool_error(tool_def.name, exc)


INFALLIBLE_TOOL_EXECUTION = InfallibleToolExecution[None]()


def format_tool_error(tool_name: str, exc: Exception) -> str:
    """Format a tool exception as a user-friendly error message for the model."""
    error_text = str(exc)

    # Extract common API error patterns
    if "402" in error_text:
        return (
            f"Tool '{tool_name}' failed: API quota exceeded (402 Payment Required). "
            "This data source is unavailable. Try using web search or a different tool."
        )
    if "401" in error_text:
        return (
            f"Tool '{tool_name}' failed: Authentication error (401). "
            "This data source is unavailable. Try using web search instead."
        )
    if "403" in error_text:
        return (
            f"Tool '{tool_name}' failed: Access denied (403 Forbidden). "
            "This data source is unavailable. Try using web search instead."
        )
    if "404" in error_text:
        return (
            f"Tool '{tool_name}' failed: Resource not found (404). "
            "The requested data does not exist. Try a different query or tool."
        )
    if "429" in error_text or "rate limit" in error_text.lower():
        return (
            f"Tool '{tool_name}' failed: Rate limit exceeded (429). "
            "Try using web search or proceed with available data."
        )
    if "timeout" in error_text.lower():
        return (
            f"Tool '{tool_name}' failed: Request timed out. "
            "The service is slow or unavailable. Try web search instead."
        )

    # Generic error
    return f"Tool '{tool_name}' failed: {error_text}. Try a different approach."
