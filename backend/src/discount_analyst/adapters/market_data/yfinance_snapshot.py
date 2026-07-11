"""Lightweight market-data helpers for exploratory valuation scripts."""

from __future__ import annotations

from typing import Any


def yfinance_snapshot(ticker: str) -> dict[str, Any]:
    """Return a JSON-serialisable current snapshot from yfinance when available."""
    try:
        import yfinance as yf  # type: ignore[reportMissingTypeStubs]
    except ImportError as exc:  # pragma: no cover - dependency is optional at runtime
        raise RuntimeError("yfinance is required for yfinance_snapshot().") from exc

    info = yf.Ticker(ticker).fast_info
    currency = getattr(info, "currency", None)
    last_price = getattr(info, "last_price", None)
    market_cap = getattr(info, "market_cap", None)
    shares = None
    if last_price not in (None, 0) and market_cap is not None:
        shares = market_cap / last_price
    return {
        "ticker": ticker,
        "currency": currency,
        "current_share_price": last_price,
        "market_cap": market_cap,
        "estimated_shares_outstanding": shares,
    }
