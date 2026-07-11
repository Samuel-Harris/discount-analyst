"""Shared system-prompt guidance for FMP/EODHD MCP tool usage."""

FINANCIAL_DATA_MCP_RULES = """
### Financial data MCP tools

FMP and EODHD MCP tools are registered when enabled for your provider. **Only call tools and endpoints that appear in your registered tool schema** — plan-gated tools and endpoints are hidden or blocked before HTTP.

If a call returns a plan-unavailable message, or a 402 or rate-limit error, do not retry that call in the same pass. Note the gap and continue with web search, primary filings, or other allowed sources.

For live price and market cap, prefer `company` with endpoint `profile-symbol`. Use `quote` with endpoint `batch-quote` only when you need supplemental intraday detail. For UK (`.L`) tickers, use EODHD `get_fundamentals_data` when FMP coverage is empty or denied.

Use `web_search` / `duckduckgo_search` and `web_fetch` for analyst coverage, news, insider activity, and detailed financial statements when MCP endpoints are unavailable.
""".strip()
