"""MCP server factories for financial data providers.

Uses MCPServerTool (built-in) so the model provider connects to MCP servers directly.
Supported providers: OpenAI Responses, Anthropic, xAI. Not supported: Google.
"""

from pydantic_ai.builtin_tools import MCPServerTool

from discount_analyst.shared.config.settings import settings

EODHD_MCP_URL = "https://mcp.eodhd.dev/mcp"
FMP_MCP_URL = "https://financialmodelingprep.com/mcp"


def create_eodhd_mcp_tool() -> MCPServerTool:
    """Create EODHD MCP server tool (historical prices, fundamentals, news, etc.)."""
    url = f"{EODHD_MCP_URL}?apikey={settings.eodhd.api_key}"
    return MCPServerTool(
        id="eodhd",
        url=url,
        description="EODHD financial data: prices, fundamentals, news, screeners",
    )


def create_fmp_mcp_tool() -> MCPServerTool:
    """Create FMP MCP server tool (quotes, financials, DCF, etc.)."""
    url = f"{FMP_MCP_URL}?apikey={settings.fmp.api_key}"
    return MCPServerTool(
        id="fmp",
        url=url,
        description="FMP financial data: quotes, statements, DCF, news",
    )


def create_financial_data_mcp_tools() -> list[MCPServerTool]:
    """Create MCP toolset with EODHD and FMP financial data tools.

    Returns:
        A list of MCPServerTool instances for builtin_tools.
    """
    return [create_eodhd_mcp_tool(), create_fmp_mcp_tool()]
