"""MCP server factories for financial data providers.

Uses MCPServerStreamableHTTP so pydantic-ai manages the MCP protocol internally and
exposes each server's tools as native function tools in the agent's tool registry.
This avoids the MCPServerTool builtin pattern where the model must call list_tools
first (injecting hundreds of tool schemas into the conversation as messages).

Supported providers: Anthropic, OpenAI. Not supported: Google (causes 400).
Use --no-mcp when running with Google models.
"""

from pydantic_ai.mcp import MCPServerStreamableHTTP

from discount_analyst.config.settings import settings

EODHD_MCP_URL = "https://mcp.eodhd.dev/mcp"
FMP_MCP_URL = "https://financialmodelingprep.com/mcp"


def create_eodhd_mcp_server() -> MCPServerStreamableHTTP:
    """Create EODHD MCP server (historical prices, fundamentals, news, etc.)."""
    url = f"{EODHD_MCP_URL}?apikey={settings.eodhd.api_key}"
    return MCPServerStreamableHTTP(url=url, tool_prefix="eodhd")


def create_fmp_mcp_server() -> MCPServerStreamableHTTP:
    """Create FMP MCP server (quotes, financials, scores, insider data, etc.)."""
    url = f"{FMP_MCP_URL}?apikey={settings.fmp.api_key}"
    return MCPServerStreamableHTTP(url=url, tool_prefix="fmp")


def create_financial_data_mcp_servers() -> list[MCPServerStreamableHTTP]:
    """Create native MCP toolsets for EODHD and FMP financial data.

    EODHD is omitted when ``EODHD__DISABLED`` is true in the root ``.env``.

    Returns:
        A list of MCPServerStreamableHTTP instances for agent toolsets.
    """
    servers: list[MCPServerStreamableHTTP] = []
    if not settings.eodhd.disabled:
        servers.append(create_eodhd_mcp_server())
    servers.append(create_fmp_mcp_server())
    return servers
