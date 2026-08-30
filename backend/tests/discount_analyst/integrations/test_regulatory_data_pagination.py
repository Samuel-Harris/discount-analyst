from datetime import UTC, datetime

import pytest

from discount_analyst.agents.tools.regulatory_data.models import EquityListing
from discount_analyst.agents.tools.regulatory_data.pagination import (
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
    page_listings,
)


def _listing(
    symbol: str, *, name: str = "Issuer", exchange: str = "NASDAQ"
) -> EquityListing:
    return EquityListing(
        symbol=symbol,
        issuer_name=name,
        exchange=exchange,
        market=exchange,
        source="nasdaq_trader",
        source_refreshed_at=datetime(2026, 8, 30, tzinfo=UTC),
    )


def test_default_page_limit_is_fifty() -> None:
    listings = [_listing(f"S{index:03d}") for index in range(80)]
    page = page_listings(listings)
    assert DEFAULT_PAGE_LIMIT == 50
    assert len(page.items) == 50
    assert page.total_count == 80
    assert page.next_cursor == "50"


def test_limit_is_capped_at_one_hundred() -> None:
    listings = [_listing(f"S{index:03d}") for index in range(150)]
    page = page_listings(listings, limit=500)
    assert MAX_PAGE_LIMIT == 100
    assert len(page.items) == 100
    assert page.next_cursor == "100"


def test_cursor_walks_remaining_rows() -> None:
    listings = [_listing(f"S{index:03d}") for index in range(12)]
    first = page_listings(listings, limit=5)
    second = page_listings(listings, limit=5, cursor=first.next_cursor)
    third = page_listings(listings, limit=5, cursor=second.next_cursor)
    assert [item.symbol for item in first.items] == [
        "S000",
        "S001",
        "S002",
        "S003",
        "S004",
    ]
    assert [item.symbol for item in second.items] == [
        "S005",
        "S006",
        "S007",
        "S008",
        "S009",
    ]
    assert [item.symbol for item in third.items] == ["S010", "S011"]
    assert third.next_cursor is None


def test_filters_combine_before_paging() -> None:
    listings = [
        _listing("AAPL", name="Apple Inc.", exchange="NASDAQ"),
        _listing("IBM", name="International Business Machines", exchange="NYSE"),
        _listing("AA", name="Alcoa Corporation", exchange="NYSE"),
        _listing("MSFT", name="Microsoft Corporation", exchange="NASDAQ"),
    ]
    page = page_listings(
        listings, exchange="NYSE", symbol_prefix="A", name_contains="alcoa"
    )
    assert page.total_count == 1
    assert page.items[0].symbol == "AA"


@pytest.mark.parametrize("limit", [0, -1])
def test_invalid_limit_raises(limit: int) -> None:
    with pytest.raises(ValueError, match="limit"):
        page_listings([_listing("AAPL")], limit=limit)
