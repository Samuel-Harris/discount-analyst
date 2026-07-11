"""Wrapper toolset that hides and short-circuits plan-gated MCP tools and endpoints."""

from dataclasses import dataclass, replace
from typing import Any

from pydantic_ai import RunContext
from pydantic_ai.toolsets.abstract import ToolsetTool
from pydantic_ai.toolsets.wrapper import WrapperToolset

from discount_analyst.agents.tools.market_data.mcp_tool_blacklist import (
    McpBlacklistPolicy,
    block_message,
    blocked_endpoints_for_tool,
    is_blocked,
    narrow_endpoint_json_schema,
)


@dataclass
class BlacklistedMcpToolset[AgentDepsT](WrapperToolset[AgentDepsT]):
    """Hide blocked tools and reject blocked endpoint calls before HTTP."""

    policy: McpBlacklistPolicy

    @property
    def id(self) -> str | None:
        return self.wrapped.id

    async def get_tools(
        self, ctx: RunContext[AgentDepsT]
    ) -> dict[str, ToolsetTool[AgentDepsT]]:
        tools = await self.wrapped.get_tools(ctx)
        return {
            name: self._with_visible_endpoint_schema(name, tool)
            for name, tool in tools.items()
            if name not in self.policy.blocked_tools
        }

    def _with_visible_endpoint_schema(
        self, name: str, tool: ToolsetTool[AgentDepsT]
    ) -> ToolsetTool[AgentDepsT]:
        blocked_endpoints = blocked_endpoints_for_tool(self.policy, name)
        if not blocked_endpoints:
            return tool

        narrowed_schema = narrow_endpoint_json_schema(
            tool.tool_def.parameters_json_schema,
            blocked_endpoints,
        )
        tool_def = replace(tool.tool_def, parameters_json_schema=narrowed_schema)
        return replace(tool, tool_def=tool_def)

    async def call_tool(
        self,
        name: str,
        tool_args: dict[str, Any],
        ctx: RunContext[AgentDepsT],
        tool: ToolsetTool[AgentDepsT],
    ) -> Any:
        if is_blocked(self.policy, name, tool_args):
            endpoint = tool_args.get("endpoint")
            endpoint_text = endpoint if isinstance(endpoint, str) else None
            return block_message(name, endpoint_text)
        return await super().call_tool(name, tool_args, ctx, tool)
