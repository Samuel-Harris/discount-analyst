"""Plan-gated MCP tool and endpoint blacklist policies."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True, slots=True)
class McpBlacklistPolicy:
    """Blacklist policy for an MCP server."""

    blocked_tools: frozenset[str] = frozenset()
    blocked_endpoints: frozenset[tuple[str, str]] = frozenset()


_FMP_BLOCKED_TOOLS = frozenset(
    {
        "analyst",
        "news",
        "insiderTrades",
        "chart",
        "calendar",
    }
)

_FMP_BLOCKED_STATEMENTS_ENDPOINTS = frozenset(
    {
        "financial-scores",
        "financial-score",
        "income-statement",
        "balance-sheet-statement",
        "cashflow-statement",
        "key-metrics",
        "enterprise-values",
        "metrics-ratios",
        "owner-earnings",
        "revenue-geographic-segments",
        "revenue-product-segmentation",
        "income-statements-ttm",
        "balance-sheet-statements-ttm",
        "cashflow-statements-ttm",
    }
)

_FMP_BLOCKED_ENDPOINTS = frozenset(
    {
        (tool_name, endpoint)
        for endpoint in _FMP_BLOCKED_STATEMENTS_ENDPOINTS
        for tool_name in ("statements",)
    }
    | {
        ("company", "batch-market-cap"),
        ("quote", "quote-short"),
    }
)

FMP_BLACKLIST = McpBlacklistPolicy(
    blocked_tools=_FMP_BLOCKED_TOOLS,
    blocked_endpoints=_FMP_BLOCKED_ENDPOINTS,
)

EODHD_BLACKLIST = McpBlacklistPolicy()


def policy_for_mcp_id(mcp_id: str) -> McpBlacklistPolicy:
    """Return the blacklist policy for a financial-data MCP server id."""
    match mcp_id:
        case "fmp":
            return FMP_BLACKLIST
        case "eodhd":
            return EODHD_BLACKLIST
        case _:
            return McpBlacklistPolicy()


def is_blocked(
    policy: McpBlacklistPolicy, tool_name: str, tool_args: dict[str, Any]
) -> bool:
    """Return whether a tool call is blocked by the policy."""
    if tool_name in policy.blocked_tools:
        return True
    endpoint = tool_args.get("endpoint")
    if isinstance(endpoint, str) and (tool_name, endpoint) in policy.blocked_endpoints:
        return True
    return False


def blocked_endpoints_for_tool(
    policy: McpBlacklistPolicy, tool_name: str
) -> frozenset[str]:
    """Return blocked endpoint values for a single multi-endpoint MCP tool."""
    return frozenset(
        endpoint
        for blocked_tool_name, endpoint in policy.blocked_endpoints
        if blocked_tool_name == tool_name
    )


def narrow_endpoint_json_schema(
    parameters_json_schema: dict[str, Any], blocked_endpoints: frozenset[str]
) -> dict[str, Any]:
    """Return a copy of a tool schema with blocked endpoint enum values removed."""
    narrowed_schema = deepcopy(parameters_json_schema)
    _remove_blocked_endpoint_values(narrowed_schema, blocked_endpoints)
    return narrowed_schema


def _remove_blocked_endpoint_values(
    schema_node: object, blocked_endpoints: frozenset[str]
) -> None:
    if not isinstance(schema_node, dict):
        return
    schema = cast(dict[str, Any], schema_node)

    properties = schema.get("properties")
    if isinstance(properties, dict):
        endpoint_schema = cast(dict[str, Any], properties).get("endpoint")
        if isinstance(endpoint_schema, dict):
            _remove_enum_values(
                cast(dict[str, Any], endpoint_schema), blocked_endpoints
            )

    for value in schema.values():
        if isinstance(value, dict):
            _remove_blocked_endpoint_values(
                cast(dict[str, Any], value), blocked_endpoints
            )
        elif isinstance(value, list):
            for item in cast(list[object], value):
                _remove_blocked_endpoint_values(item, blocked_endpoints)


def _remove_enum_values(
    schema_node: dict[str, Any], blocked_values: frozenset[str]
) -> None:
    enum_values = schema_node.get("enum")
    if isinstance(enum_values, list):
        schema_node["enum"] = [
            value
            for value in cast(list[object], enum_values)
            if not (isinstance(value, str) and value in blocked_values)
        ]

    for keyword in ("anyOf", "oneOf", "allOf"):
        variants = schema_node.get(keyword)
        if isinstance(variants, list):
            for variant in cast(list[object], variants):
                if isinstance(variant, dict):
                    _remove_enum_values(cast(dict[str, Any], variant), blocked_values)


def block_message(tool_name: str, endpoint: str | None) -> str:
    """Return a model-facing message for a blocked tool call."""
    if endpoint:
        return (
            f"Tool '{tool_name}' endpoint '{endpoint}' is unavailable on the current data plan "
            "and is not offered. Do not retry this endpoint; use an allowed tool or web search instead."
        )
    return (
        f"Tool '{tool_name}' is unavailable on the current data plan and is not offered. "
        "Do not retry this tool; use an allowed tool or web search instead."
    )
