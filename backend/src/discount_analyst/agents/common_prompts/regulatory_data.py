"""Shared system-prompt guidance for official exchange and filing tools."""

REGULATORY_UNIVERSE_TOOL_RULES = """
### Official universe tools

`list_us_listed_equities` and `list_uk_listed_equities` enumerate currently listed ordinary
equities from NASDAQ Trader and the official LSE issuers report. Use them to confirm official
exchange membership for candidates found with yfinance; they do not supply market capitalisation,
liquidity, or ratios.

Results default to 50 rows and cap at 100. Use the returned opaque `next_cursor` only when another
page is required; apply `exchange` / `market`, `symbol_prefix`, or `name_contains` filters whenever
possible instead of loading an unbounded universe into context. The US list can still contain an
acquisition company's ordinary shares, so enforce the no-SPAC rule separately.

If a listing call reports a missing or incomplete cache, record that listing membership could not
be confirmed and continue. Do not retry it or substitute a paid screener.
""".strip()

REGULATORY_FILINGS_TOOL_RULES = """
### Official filing tools

Read-only tools against locally cached official sources:

- `get_sec_company_facts(ticker, period_kind="annual"|"quarterly", as_of=None)` — one US 10-K/10-Q snapshot plus up to five recent filing handles. Amended filings win for the same period. Missing tags stay null; do not invent them.
- `resolve_uk_company(query)` — company number, exact registered name, or TIDM (TIDM only when an LSE issuers snapshot is already cached). If `selected` is absent, the match is missing or ambiguous; do not guess.
- `get_companies_house_accounts(company_number, as_of=None)` — UK accounts. Filleted accounts set `accounts_filleted=true` and leave P&L fields null; never infer revenue or profit.

If a call reports a missing cache, record the gap and continue. Do not scrape unofficial substitutes in a retry loop.
""".strip()
