"""Plan-gated MCP tool and endpoint blacklist policies."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, TypeIs


def _is_json_object(node: object) -> TypeIs[dict[str, Any]]:
    return isinstance(node, dict)


def _is_json_array(node: object) -> TypeIs[list[Any]]:
    return isinstance(node, list)


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
    """Return a copy of a tool schema with blocked ``properties.endpoint`` enum values removed."""
    narrowed_schema = deepcopy(parameters_json_schema)
    properties = narrowed_schema.get("properties")
    if not _is_json_object(properties):
        return narrowed_schema

    endpoint_schema = properties.get("endpoint")
    if _is_json_object(endpoint_schema):
        _strip_blocked_endpoint_enums(endpoint_schema, blocked_endpoints)
    return narrowed_schema


def _strip_blocked_endpoint_enums(
    endpoint_schema: dict[str, Any], blocked_endpoints: frozenset[str]
) -> None:
    """Strip blocked values from an endpoint parameter schema (enum / anyOf / oneOf / allOf)."""
    enum_values = endpoint_schema.get("enum")
    if _is_json_array(enum_values):
        endpoint_schema["enum"] = [
            value
            for value in enum_values
            if not (isinstance(value, str) and value in blocked_endpoints)
        ]

    for keyword in ("anyOf", "oneOf", "allOf"):
        variants = endpoint_schema.get(keyword)
        if not _is_json_array(variants):
            continue
        for variant in variants:
            if _is_json_object(variant):
                _strip_blocked_endpoint_enums(variant, blocked_endpoints)


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
