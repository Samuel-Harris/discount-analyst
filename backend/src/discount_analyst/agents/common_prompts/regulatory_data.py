"""Shared system-prompt guidance for official exchange and filing tools."""

REGULATORY_UNIVERSE_TOOL_RULES = """
### Official universe tools (£0)

`list_us_listed_equities` and `list_uk_listed_equities` enumerate currently listed ordinary equities from NASDAQ Trader and the official LSE issuers report. They confirm that a symbol is a listed common equity and can page a prefix of the universe. They are a complement to FMP/EODHD MCP screeners, not a replacement: keep using those screeners for market-cap, liquidity, and ratio filters.
""".strip()

REGULATORY_FILINGS_TOOL_RULES = """
### Official filing tools (£0)

Read-only tools against locally cached official sources (no paid keys):

- `get_sec_company_facts(ticker, period_kind="annual"|"quarterly", as_of=None)` — one US 10-K/10-Q snapshot plus up to five recent filing handles. Amended filings win for the same period. Missing tags stay null; do not invent them.
- `resolve_uk_company(query)` — company number, exact registered name, or TIDM (TIDM only when an LSE issuers snapshot is already cached). If `selected` is absent, the match is missing or ambiguous; do not guess.
- `get_companies_house_accounts(company_number, as_of=None)` — UK accounts. Filleted accounts set `accounts_filleted=true` and leave P&L fields null; never infer revenue or profit.

If a call reports a missing cache, record the gap and continue. Do not scrape unofficial substitutes in a retry loop.
""".strip()
