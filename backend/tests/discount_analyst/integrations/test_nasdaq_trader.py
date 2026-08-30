from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import httpx
import pytest

from discount_analyst.agents.tools.regulatory_data.cache import RegulatoryDataCache
from discount_analyst.agents.tools.regulatory_data.errors import (
    ColdCacheError,
    SchemaValidationError,
)
from discount_analyst.agents.tools.regulatory_data.exchanges import (
    nasdaq_trader as nasdaq_module,
)
from discount_analyst.agents.tools.regulatory_data.exchanges.nasdaq_trader import (
    list_us_listed_equities,
    refresh_nasdaq_trader,
)
from discount_analyst.agents.tools.regulatory_data.models import CacheSource, UsExchange

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "regulatory_data"
NASDAQ_LISTED_FIXTURE = FIXTURE_DIR / "nasdaq" / "nasdaqlisted.txt"
NASDAQ_OTHER_LISTED_FIXTURE = FIXTURE_DIR / "nasdaq" / "otherlisted.txt"

EXPECTED_SURVIVORS = {
    "AAPL": (UsExchange.NASDAQ, "NASDAQ GS"),
    "MSFT": (UsExchange.NASDAQ, "NASDAQ GS"),
    "IBM": (UsExchange.NYSE, "NYSE"),
    "BA": (UsExchange.NYSE, "NYSE"),
    "NEM": (UsExchange.NYSE, "NYSE"),
    "UEC": (UsExchange.NYSE_AMERICAN, "NYSE American"),
}
REJECTED_SYMBOLS = {
    "QQQ",
    "ZZZZ",
    "ACIW",
    "ABCD",
    "SPY",
    "AA-P",
    "XYZ.WS",
    "NOTE1",
}


def _install_mock_client(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[[httpx.Request], httpx.Response],
) -> list[httpx.Request]:
    requests: list[httpx.Request] = []

    def transport_handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    def fake_create_metadata_client() -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(transport_handler))

    monkeypatch.setattr(
        nasdaq_module, "create_metadata_client", fake_create_metadata_client
    )
    return requests


def _bind_cache(monkeypatch: pytest.MonkeyPatch, cache: RegulatoryDataCache) -> None:
    def from_settings(cls: type[RegulatoryDataCache]) -> RegulatoryDataCache:
        return cache

    monkeypatch.setattr(
        RegulatoryDataCache, "from_settings", classmethod(from_settings)
    )


def _fixture_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path.endswith("nasdaqlisted.txt"):
        return httpx.Response(
            200, content=NASDAQ_LISTED_FIXTURE.read_bytes(), request=request
        )
    if path.endswith("otherlisted.txt"):
        return httpx.Response(
            200, content=NASDAQ_OTHER_LISTED_FIXTURE.read_bytes(), request=request
        )
    return httpx.Response(404, request=request)


def _poison_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(503, request=request)


def _wrong_header_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("nasdaqlisted.txt"):
        body = "Nope|Wrong Header\nAAPL|Apple Inc. - Common Stock|Q|N|N|100|N|N\n"
        return httpx.Response(200, content=body.encode(), request=request)
    return _fixture_handler(request)


async def test_nasdaq_merge_filter_and_exchange_mapping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    _install_mock_client(monkeypatch, _fixture_handler)

    result = await refresh_nasdaq_trader()
    page = await list_us_listed_equities()

    by_symbol = {item.symbol: item for item in page.items}
    assert set(by_symbol) == set(EXPECTED_SURVIVORS)
    assert REJECTED_SYMBOLS.isdisjoint(by_symbol)
    for symbol, (exchange, market) in EXPECTED_SURVIVORS.items():
        listing = by_symbol[symbol]
        assert listing.exchange == exchange
        assert listing.market == market
        assert listing.isin is None
        assert listing.source == CacheSource.NASDAQ_TRADER
        snapshot = cache.snapshot_for(CacheSource.NASDAQ_TRADER)
        assert snapshot is not None
        assert listing.source_refreshed_at == snapshot.refreshed_at
    assert result.record_count == len(EXPECTED_SURVIVORS)
    assert by_symbol["AAPL"].exchange == "NASDAQ"
    assert by_symbol["IBM"].exchange == "NYSE"
    assert by_symbol["UEC"].exchange == "NYSE American"


async def test_list_us_listed_equities_paginates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    _install_mock_client(monkeypatch, _fixture_handler)
    await refresh_nasdaq_trader()

    first = await list_us_listed_equities(limit=2)
    second = await list_us_listed_equities(limit=2, cursor=first.next_cursor)
    third = await list_us_listed_equities(limit=2, cursor=second.next_cursor)

    assert first.total_count == 6
    assert [item.symbol for item in first.items] == ["AAPL", "MSFT"]
    assert first.next_cursor == "2"
    assert [item.symbol for item in second.items] == ["IBM", "BA"]
    assert second.next_cursor == "4"
    assert [item.symbol for item in third.items] == ["NEM", "UEC"]
    assert third.next_cursor is None
    assert second.total_count == first.total_count == third.total_count == 6


async def test_stale_nasdaq_snapshot_is_served_when_refresh_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    _install_mock_client(monkeypatch, _fixture_handler)
    await refresh_nasdaq_trader()
    _install_mock_client(monkeypatch, _poison_handler)

    def never_fresh(
        self: RegulatoryDataCache,
        source: CacheSource | str,
        *,
        ttl: timedelta = timedelta(hours=24),
    ) -> bool:
        return False

    monkeypatch.setattr(RegulatoryDataCache, "is_fresh", never_fresh)

    page = await list_us_listed_equities()
    assert {item.symbol for item in page.items} == set(EXPECTED_SURVIVORS)


async def test_changed_nasdaq_header_keeps_previous_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    _install_mock_client(monkeypatch, _fixture_handler)
    first = await refresh_nasdaq_trader()
    _install_mock_client(monkeypatch, _wrong_header_handler)

    with pytest.raises(SchemaValidationError, match="nasdaqlisted.txt header"):
        await refresh_nasdaq_trader()

    assert cache.load_manifest().sources["nasdaq_trader"].version_id == first.version_id
    page = await list_us_listed_equities()
    assert {item.symbol for item in page.items} == set(EXPECTED_SURVIVORS)


async def test_cold_nasdaq_cache_names_refresh_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    _install_mock_client(monkeypatch, _poison_handler)

    with pytest.raises(
        ColdCacheError,
        match=r"discount-analyst admin refresh-regulatory-data --exchanges",
    ):
        await list_us_listed_equities()
