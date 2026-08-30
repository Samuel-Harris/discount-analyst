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
    london_stock_exchange as lse_module,
)
from discount_analyst.agents.tools.regulatory_data.exchanges.london_stock_exchange import (
    LSE_ISSUERS_REPORT_LABEL,
    list_uk_listed_equities,
    refresh_lse_issuers,
)
from discount_analyst.agents.tools.regulatory_data.models import CacheSource, UkMarket

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "regulatory_data"
LSE_REPORTS_PAGE_FIXTURE = FIXTURE_DIR / "lse" / "reports_issuers.html"
LSE_ISSUERS_REPORT_FIXTURE = FIXTURE_DIR / "lse" / "issuers_report.csv"

EXPECTED_MARKETS = {
    "AZN": UkMarket.MAIN,
    "SBRY": UkMarket.MAIN,
    "GHH": UkMarket.AIM,
    "QQ.": UkMarket.MAIN,
    "BILB": UkMarket.AIM,
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
        lse_module, "create_metadata_client", fake_create_metadata_client
    )
    return requests


def _bind_cache(monkeypatch: pytest.MonkeyPatch, cache: RegulatoryDataCache) -> None:
    def from_settings(cls: type[RegulatoryDataCache]) -> RegulatoryDataCache:
        return cache

    monkeypatch.setattr(
        RegulatoryDataCache, "from_settings", classmethod(from_settings)
    )


def _fixture_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/reports":
        return httpx.Response(
            200,
            content=LSE_REPORTS_PAGE_FIXTURE.read_bytes(),
            headers={"content-type": "text/html"},
            request=request,
        )
    if request.url.path.endswith("issuer-list.csv"):
        return httpx.Response(
            200,
            content=LSE_ISSUERS_REPORT_FIXTURE.read_bytes(),
            headers={"content-type": "text/csv"},
            request=request,
        )
    return httpx.Response(404, request=request)


def _poison_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(503, request=request)


def _wrong_header_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/reports":
        return _fixture_handler(request)
    body = "Ticker,Name,ISIN,Market,Instrument name,Sector\nAZN,AstraZeneca PLC,GB0009895292,MAIN MARKET,Ordinary Shares,Pharmaceuticals\n"
    return httpx.Response(200, content=body.encode(), request=request)


def _js_shell_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/reports":
        return httpx.Response(
            200,
            content=b'<!DOCTYPE html><html lang="en"><body></body></html>',
            headers={"content-type": "text/html"},
            request=request,
        )
    return httpx.Response(404, request=request)


async def test_lse_main_and_aim_parsing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    requests = _install_mock_client(monkeypatch, _fixture_handler)

    result = await refresh_lse_issuers()
    page = await list_uk_listed_equities()

    by_symbol = {item.symbol: item for item in page.items}
    assert set(by_symbol) == set(EXPECTED_MARKETS)
    for symbol, market in EXPECTED_MARKETS.items():
        listing = by_symbol[symbol]
        assert listing.exchange == "LSE"
        assert listing.market == market
        assert listing.source == CacheSource.LSE_ISSUERS
        assert listing.isin
    assert by_symbol["AZN"].market == "Main"
    assert by_symbol["GHH"].market == "AIM"
    assert by_symbol["QQ."].symbol == "QQ."
    assert result.record_count == len(EXPECTED_MARKETS)
    requested_urls = [str(request.url) for request in requests]
    assert any("tab=issuers" in url for url in requested_urls)
    assert any(url.endswith("/reports/issuer-list.csv") for url in requested_urls)
    assert LSE_ISSUERS_REPORT_LABEL not in "".join(requested_urls)


async def test_list_uk_listed_equities_paginates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    _install_mock_client(monkeypatch, _fixture_handler)
    await refresh_lse_issuers()

    first = await list_uk_listed_equities(limit=2)
    second = await list_uk_listed_equities(limit=2, cursor=first.next_cursor)
    third = await list_uk_listed_equities(limit=2, cursor=second.next_cursor)

    assert first.total_count == 5
    assert [item.symbol for item in first.items] == ["AZN", "SBRY"]
    assert first.next_cursor == "2"
    assert [item.symbol for item in second.items] == ["GHH", "QQ."]
    assert second.next_cursor == "4"
    assert [item.symbol for item in third.items] == ["BILB"]
    assert third.next_cursor is None
    assert second.total_count == first.total_count == third.total_count == 5


async def test_stale_lse_snapshot_is_served_when_refresh_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    _install_mock_client(monkeypatch, _fixture_handler)
    await refresh_lse_issuers()
    _install_mock_client(monkeypatch, _poison_handler)

    def never_fresh(
        self: RegulatoryDataCache,
        source: CacheSource | str,
        *,
        ttl: timedelta = timedelta(hours=24),
    ) -> bool:
        return False

    monkeypatch.setattr(RegulatoryDataCache, "is_fresh", never_fresh)

    page = await list_uk_listed_equities()
    assert {item.symbol for item in page.items} == set(EXPECTED_MARKETS)


async def test_changed_lse_header_keeps_previous_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    _install_mock_client(monkeypatch, _fixture_handler)
    first = await refresh_lse_issuers()
    _install_mock_client(monkeypatch, _wrong_header_handler)

    with pytest.raises(SchemaValidationError, match="issuers report header"):
        await refresh_lse_issuers()

    assert cache.load_manifest().sources["lse_issuers"].version_id == first.version_id
    page = await list_uk_listed_equities()
    assert {item.symbol for item in page.items} == set(EXPECTED_MARKETS)


async def test_cold_lse_cache_names_refresh_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    _install_mock_client(monkeypatch, _poison_handler)

    with pytest.raises(
        ColdCacheError,
        match=r"discount-analyst admin refresh-regulatory-data --exchanges",
    ):
        await list_uk_listed_equities()


async def test_js_shell_reports_page_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    _install_mock_client(monkeypatch, _js_shell_handler)

    with pytest.raises(SchemaValidationError, match="found 0"):
        await refresh_lse_issuers()
