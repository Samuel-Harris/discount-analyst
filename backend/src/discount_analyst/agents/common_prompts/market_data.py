"""Shared system-prompt guidance for market-data source selection."""

MARKET_DATA_TOOL_RULES = """
### Market-data source order

When `terminal_exec` is available, use yfinance as the primary source for current price,
currency, market capitalisation, shares outstanding, and price history. Use short, bounded
Python commands:

- Access `Ticker.fast_info` values as attributes such as `last_price`, `market_cap`, and
  `currency`; do not use `.get()` on the lazy object.
- Use `Ticker.history(..., auto_adjust=False)` when the quoted close must remain auditable.
  Treat empty frames and null rows as missing data, not zero.
- Use `Ticker.get_shares_full()` or `Ticker.info["sharesOutstanding"]` to cross-check the
  share count. Reconcile price × shares with market capitalisation before relying on it.
- For `.L` tickers, yfinance quotes `fast_info` price and market capitalisation in GBp.
  `Ticker.info["marketCap"]` and screener `marketCap` are in major GBP. Convert subunits
  exactly once and state the convention used.

FMP and EODHD are optional paid fallbacks, not the default source. Never use their screeners,
live-price, historical-price, or market-cap endpoints. Call a registered non-screening endpoint
only when yfinance, an official filing, and issuer material leave a material gap that the endpoint
can answer. Make one attempt; on a plan, 402, empty, or rate-limit response, record the gap and
continue without retrying another paid variant.
""".strip()
