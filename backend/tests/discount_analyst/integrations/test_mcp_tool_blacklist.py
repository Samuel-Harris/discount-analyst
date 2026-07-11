"""Tests for MCP tool blacklist policy and wrapper."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic_ai import RunContext
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.toolsets.abstract import AbstractToolset, ToolsetTool

from discount_analyst.agents.tools.market_data.blacklisted_mcp_toolset import (
    BlacklistedMcpToolset,
)
from discount_analyst.agents.tools.market_data.mcp_tool_blacklist import (
    EODHD_BLACKLIST,
    FMP_BLACKLIST,
    McpBlacklistPolicy,
    block_message,
    blocked_endpoints_for_tool,
    is_blocked,
    narrow_endpoint_json_schema,
    policy_for_mcp_id,
)


def test_is_blocked_whole_tool() -> None:
    assert is_blocked(FMP_BLACKLIST, "analyst", {"endpoint": "ratings-snapshot"})
    assert not is_blocked(FMP_BLACKLIST, "search", {"endpoint": "search-symbol"})


def test_is_blocked_endpoint_pair() -> None:
    assert is_blocked(
        FMP_BLACKLIST,
        "statements",
        {"endpoint": "financial-scores"},
    )
    assert not is_blocked(
        FMP_BLACKLIST,
        "statements",
        {"endpoint": "financial-reports-dates"},
    )
    assert is_blocked(FMP_BLACKLIST, "quote", {"endpoint": "quote-short"})
    assert not is_blocked(FMP_BLACKLIST, "quote", {"endpoint": "batch-quote"})


def test_is_blocked_without_endpoint_only_checks_whole_tool() -> None:
    assert not is_blocked(FMP_BLACKLIST, "company", {"symbol": "AAPL"})
    assert is_blocked(FMP_BLACKLIST, "news", {})


def test_blocked_endpoints_for_tool() -> None:
    assert blocked_endpoints_for_tool(FMP_BLACKLIST, "company") == frozenset(
        {"batch-market-cap"}
    )
    assert blocked_endpoints_for_tool(FMP_BLACKLIST, "search") == frozenset()


def test_narrow_endpoint_json_schema_removes_blocked_endpoint_enum_values() -> None:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "endpoint": {
                "type": "string",
                "enum": ["profile-symbol", "batch-market-cap"],
            }
        },
    }

    narrowed_schema = narrow_endpoint_json_schema(
        schema, frozenset({"batch-market-cap"})
    )

    assert narrowed_schema["properties"]["endpoint"]["enum"] == ["profile-symbol"]
    assert schema["properties"]["endpoint"]["enum"] == [
        "profile-symbol",
        "batch-market-cap",
    ]


def test_narrow_endpoint_json_schema_strips_any_of_endpoint_enums() -> None:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "endpoint": {
                "anyOf": [
                    {"type": "string", "enum": ["profile-symbol", "batch-market-cap"]},
                    {"type": "null"},
                ]
            }
        },
    }

    narrowed_schema = narrow_endpoint_json_schema(
        schema, frozenset({"batch-market-cap"})
    )

    assert narrowed_schema["properties"]["endpoint"]["anyOf"][0]["enum"] == [
        "profile-symbol"
    ]


def test_block_message_with_and_without_endpoint() -> None:
    assert "financial-scores" in block_message("statements", "financial-scores")
    assert "not offered" in block_message("analyst", None).lower()


def test_policy_for_mcp_id() -> None:
    assert policy_for_mcp_id("fmp") is FMP_BLACKLIST
    assert policy_for_mcp_id("eodhd") is EODHD_BLACKLIST
    assert policy_for_mcp_id("unknown") == McpBlacklistPolicy()


def test_eodhd_blacklist_is_empty() -> None:
    assert EODHD_BLACKLIST.blocked_tools == frozenset()
    assert EODHD_BLACKLIST.blocked_endpoints == frozenset()


def _toolset_tool(
    name: str, parameters_json_schema: dict[str, Any] | None = None
) -> ToolsetTool[None]:
    tool_def = ToolDefinition(
        name=name,
        description=f"{name} tool",
        parameters_json_schema=parameters_json_schema
        or {"type": "object", "properties": {}},
    )
    return ToolsetTool(
        toolset=MagicMock(spec=AbstractToolset),
        tool_def=tool_def,
        max_retries=0,
        args_validator=MagicMock(),  # type: ignore[arg-type]
    )


def _blacklisted_toolset(wrapped: AbstractToolset[None]) -> BlacklistedMcpToolset[None]:
    return BlacklistedMcpToolset[None](wrapped, policy=FMP_BLACKLIST)


def _run_context() -> RunContext[None]:
    return cast(RunContext[None], MagicMock(spec=RunContext))


@pytest.mark.asyncio
async def test_blacklisted_mcp_toolset_get_tools_omits_blocked_tools() -> None:
    wrapped = MagicMock(spec=AbstractToolset)
    wrapped.id = "fmp"
    wrapped.get_tools = AsyncMock(
        return_value={
            "search": _toolset_tool("search"),
            "analyst": _toolset_tool("analyst"),
            "company": _toolset_tool("company"),
        }
    )
    toolset = _blacklisted_toolset(wrapped)
    ctx = _run_context()

    tools = await toolset.get_tools(ctx)

    assert set(tools) == {"search", "company"}


@pytest.mark.asyncio
async def test_blacklisted_mcp_toolset_get_tools_removes_blocked_endpoint_values() -> (
    None
):
    wrapped = MagicMock(spec=AbstractToolset)
    wrapped.id = "fmp"
    original_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "endpoint": {
                "type": "string",
                "enum": ["profile-symbol", "batch-market-cap"],
            },
            "symbol": {"type": "string"},
        },
    }
    wrapped.get_tools = AsyncMock(
        return_value={"company": _toolset_tool("company", original_schema)}
    )
    toolset = _blacklisted_toolset(wrapped)
    ctx = _run_context()

    tools = await toolset.get_tools(ctx)

    endpoint_schema = tools["company"].tool_def.parameters_json_schema["properties"][
        "endpoint"
    ]
    assert endpoint_schema["enum"] == ["profile-symbol"]
    assert original_schema["properties"]["endpoint"]["enum"] == [
        "profile-symbol",
        "batch-market-cap",
    ]


@pytest.mark.asyncio
async def test_blacklisted_mcp_toolset_call_tool_short_circuits_blocked_endpoint() -> (
    None
):
    wrapped = MagicMock(spec=AbstractToolset)
    wrapped.id = "fmp"
    toolset = _blacklisted_toolset(wrapped)
    ctx = _run_context()
    tool = _toolset_tool("statements")

    with patch(
        "discount_analyst.agents.tools.market_data.blacklisted_mcp_toolset.WrapperToolset.call_tool",
        new_callable=AsyncMock,
    ) as delegate_call:
        result = await toolset.call_tool(
            "statements",
            {"endpoint": "financial-scores"},
            ctx,
            tool,
        )

    assert "financial-scores" in result
    delegate_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_blacklisted_mcp_toolset_call_tool_delegates_allowed_endpoint() -> None:
    wrapped = MagicMock(spec=AbstractToolset)
    wrapped.id = "fmp"
    toolset = _blacklisted_toolset(wrapped)
    ctx = _run_context()
    tool = _toolset_tool("company")
    expected: dict[str, Any] = {"symbol": "AAPL"}

    with patch(
        "discount_analyst.agents.tools.market_data.blacklisted_mcp_toolset.WrapperToolset.call_tool",
        new_callable=AsyncMock,
        return_value=expected,
    ) as delegate_call:
        result = await toolset.call_tool(
            "company",
            {"endpoint": "profile-symbol", "symbol": "AAPL"},
            ctx,
            tool,
        )

    assert result == expected
    delegate_call.assert_awaited_once()


def test_blacklisted_mcp_toolset_preserves_wrapped_id() -> None:
    wrapped = MagicMock(spec=AbstractToolset)
    wrapped.id = "eodhd"
    toolset = BlacklistedMcpToolset[None](wrapped, policy=EODHD_BLACKLIST)
    assert toolset.id == "eodhd"
