from collections.abc import Sequence

from discount_analyst.agents.tools.regulatory_data.models import (
    EquityListing,
    ListedEquitiesPage,
)

DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 100


def normalise_page_limit(limit: int) -> int:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    return min(limit, MAX_PAGE_LIMIT)


def parse_offset_cursor(cursor: str | None) -> int:
    if cursor is None or cursor == "":
        return 0
    try:
        offset = int(cursor)
    except ValueError as exc:
        raise ValueError(f"cursor must be an integer offset, got {cursor!r}") from exc
    if offset < 0:
        raise ValueError("cursor offset must be >= 0")
    return offset


def next_offset_cursor(*, offset: int, limit: int, total_count: int) -> str | None:
    nxt = offset + limit
    if nxt >= total_count:
        return None
    return str(nxt)


def normalise_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def filter_listings(
    listings: Sequence[EquityListing],
    *,
    exchange: str | None = None,
    market: str | None = None,
    symbol_prefix: str | None = None,
    name_contains: str | None = None,
) -> list[EquityListing]:
    exchange_filter = exchange.strip().casefold() if exchange else None
    market_filter = market.strip().casefold() if market else None
    prefix = normalise_symbol(symbol_prefix) if symbol_prefix else None
    name_filter = name_contains.strip().casefold() if name_contains else None

    matched: list[EquityListing] = []
    for listing in listings:
        if exchange_filter and listing.exchange.casefold() != exchange_filter:
            continue
        if market_filter and listing.market.casefold() != market_filter:
            continue
        if prefix and not normalise_symbol(listing.symbol).startswith(prefix):
            continue
        if name_filter and name_filter not in listing.issuer_name.casefold():
            continue
        matched.append(listing)
    return matched


def page_listings(
    listings: Sequence[EquityListing],
    *,
    exchange: str | None = None,
    market: str | None = None,
    symbol_prefix: str | None = None,
    name_contains: str | None = None,
    limit: int = DEFAULT_PAGE_LIMIT,
    cursor: str | None = None,
) -> ListedEquitiesPage:
    page_limit = normalise_page_limit(limit)
    offset = parse_offset_cursor(cursor)
    matched = filter_listings(
        listings,
        exchange=exchange,
        market=market,
        symbol_prefix=symbol_prefix,
        name_contains=name_contains,
    )
    total_count = len(matched)
    sliced = matched[offset : offset + page_limit]
    return ListedEquitiesPage(
        items=sliced,
        total_count=total_count,
        next_cursor=next_offset_cursor(
            offset=offset, limit=page_limit, total_count=total_count
        ),
    )
