"""MCP server factories for financial data providers.

Uses MCPToolset so pydantic-ai manages the MCP protocol internally and exposes each
server's tools as native function tools in the agent's tool registry. This avoids the
MCPServerTool builtin pattern where the model must call list_tools first (injecting
hundreds of tool schemas into the conversation as messages).

Supported providers: Anthropic, OpenAI, DeepSeek. Not supported: Google (causes 400).
Use --no-mcp when running with Google models.
"""

from pydantic_ai.mcp import MCPToolset
from pydantic_ai.toolsets.abstract import AbstractToolset

from discount_analyst.config.settings import settings
from discount_analyst.agents.tools.market_data.blacklisted_mcp_toolset import (
    BlacklistedMcpToolset,
)
from discount_analyst.agents.tools.market_data.mcp_tool_blacklist import (
    policy_for_mcp_id,
)

EODHD_MCP_URL = "https://mcp.eodhd.dev/mcp"
FMP_MCP_URL = "https://financialmodelingprep.com/mcp"


def wrap_mcp_server(server: MCPToolset) -> BlacklistedMcpToolset[None]:
    """Apply the plan-gated blacklist policy for the server's MCP id."""
    mcp_id = server.id or ""
    return BlacklistedMcpToolset(server, policy=policy_for_mcp_id(mcp_id))


def create_eodhd_mcp_server() -> BlacklistedMcpToolset[None]:
    """Create EODHD MCP server (historical prices, fundamentals, news, etc.)."""
    url = f"{EODHD_MCP_URL}?apikey={settings.eodhd.api_key}"
    return wrap_mcp_server(MCPToolset(url, id="eodhd"))


def create_fmp_mcp_server() -> BlacklistedMcpToolset[None]:
    """Create FMP MCP server (quotes, financials, scores, insider data, etc.)."""
    url = f"{FMP_MCP_URL}?apikey={settings.fmp.api_key}"
    return wrap_mcp_server(MCPToolset(url, id="fmp"))


def create_financial_data_mcp_servers() -> list[AbstractToolset[None]]:
    """Create native MCP toolsets for EODHD and FMP financial data.

    EODHD is omitted when ``EODHD__DISABLED`` is true in the root ``.env``.

    Returns:
        A list of blacklist-wrapped MCP toolsets for agent toolsets.
    """
    servers: list[AbstractToolset[None]] = []
    if not settings.eodhd.disabled:
        servers.append(create_eodhd_mcp_server())
    servers.append(create_fmp_mcp_server())
    return servers
