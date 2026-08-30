from __future__ import annotations

import json
from collections.abc import Callable
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZipFile

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
    LSE_INSTRUMENT_LIST_CTA_TITLE,
    list_uk_listed_equities,
    refresh_lse_issuers,
)
from discount_analyst.agents.tools.regulatory_data.models import CacheSource, UkMarket

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "regulatory_data"
LSE_REPORTS_PAGES_FIXTURE = FIXTURE_DIR / "lse" / "reports_pages.json"
LSE_INSTRUMENTS_REFRESH_FIXTURE = FIXTURE_DIR / "lse" / "instruments_refresh.json"

EXPECTED_MARKETS = {
    "AZN": UkMarket.MAIN,
    "SBRY": UkMarket.MAIN,
    "GHH": UkMarket.AIM,
    "QQ.": UkMarket.MAIN,
    "BILB": UkMarket.AIM,
}

_PAGES_JSON = json.loads(LSE_REPORTS_PAGES_FIXTURE.read_text())
_REFRESH_JSON = json.loads(LSE_INSTRUMENTS_REFRESH_FIXTURE.read_text())
_INSTRUMENT_LIST_PATH = "/sites/default/files/reports/instrument-list.xlsx"


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


def _xlsx_inline_sheet(rows: list[list[str]]) -> bytes:
    xml_rows: list[str] = []
    for row_number, cells in enumerate(rows, start=1):
        xml_cells: list[str] = []
        for column_index, value in enumerate(cells):
            column = chr(ord("A") + column_index)
            xml_cells.append(
                f'<c r="{column}{row_number}" t="inlineStr">'
                f"<is><t>{escape(value)}</t></is></c>"
            )
        xml_rows.append(f'<row r="{row_number}">{"".join(xml_cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(xml_rows)}</sheetData></worksheet>"
    ).encode()


def _instrument_list_xlsx_bytes(*, shares_header: list[str] | None = None) -> bytes:
    header = shares_header or [
        "TIDM",
        "Issuer Name",
        "Instrument Name",
        "ISIN",
        "LSE Market",
    ]
    equity_rows = [
        header,
        ["AZN", "AstraZeneca PLC", "ORD USD0.25", "GB0009895292", "MAIN MARKET"],
        ["SBRY", "J Sainsbury PLC", "ORD 28 4/7P", "GB00B019KW72", "MAIN MARKET"],
        ["GHH", "Gooch & Housego PLC", "ORD 20P", "GB0002259116", "AIM"],
        ["QQ.", "QinetiQ Group PLC", "ORD 1P", "GB00B0WMWD43", "MAIN MARKET"],
        ["BILB", "Bilby PLC", "ORD 10P", "GB00BYZJQT16", "AIM"],
    ]
    etf_rows = [
        header,
        ["ARAW", "ETF ISSUER PLC", "UCITS ETF", "IE000J7QYHD8", "MAIN MARKET"],
    ]
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                "<Types "
                'xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" '
                'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                "</Types>"
            ),
        )
        archive.writestr(
            "xl/workbook.xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                "<workbook "
                'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                "<sheets>"
                '<sheet name="1.0 All Equity" sheetId="1" r:id="rId1"/>'
                '<sheet name="1.1 Shares" sheetId="2" r:id="rId2"/>'
                "</sheets></workbook>"
            ),
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                "<Relationships "
                'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                'Target="worksheets/sheet1.xml"/>'
                '<Relationship Id="rId2" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                'Target="worksheets/sheet2.xml"/>'
                "</Relationships>"
            ),
        )
        archive.writestr("xl/worksheets/sheet1.xml", _xlsx_inline_sheet(etf_rows))
        archive.writestr(
            "xl/worksheets/sheet2.xml",
            _xlsx_inline_sheet(
                [["All Equity Instruments"], ["As at 31 July 2026"], [], *equity_rows]
            ),
        )
    return buffer.getvalue()


def _fixture_handler(request: httpx.Request) -> httpx.Response:
    if request.method == "GET" and request.url.path == "/api/v1/pages":
        return httpx.Response(200, json=_PAGES_JSON, request=request)
    if request.method == "POST" and request.url.path == "/api/v1/components/refresh":
        return httpx.Response(200, json=_REFRESH_JSON, request=request)
    if request.url.path == _INSTRUMENT_LIST_PATH:
        return httpx.Response(
            200,
            content=_instrument_list_xlsx_bytes(),
            headers={
                "content-type": (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            },
            request=request,
        )
    return httpx.Response(404, request=request)


def _poison_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(503, request=request)


def _wrong_header_handler(request: httpx.Request) -> httpx.Response:
    if request.method == "GET" and request.url.path == "/api/v1/pages":
        return _fixture_handler(request)
    if request.method == "POST" and request.url.path == "/api/v1/components/refresh":
        return _fixture_handler(request)
    return httpx.Response(
        200,
        content=_instrument_list_xlsx_bytes(
            shares_header=[
                "Ticker",
                "Name",
                "ISIN",
                "LSE Market",
                "Instrument Name",
            ]
        ),
        headers={
            "content-type": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        },
        request=request,
    )


def _empty_cms_handler(request: httpx.Request) -> httpx.Response:
    if request.method == "GET" and request.url.path == "/api/v1/pages":
        return httpx.Response(200, json={}, request=request)
    return httpx.Response(404, request=request)


def _html_reports_page_handler(request: httpx.Request) -> httpx.Response:
    if request.url.host == "www.londonstockexchange.com":
        return httpx.Response(
            200,
            content=b"<!DOCTYPE html><html><body><a href='/reports/issuer-list.csv'>Issuer list</a></body></html>",
            headers={"content-type": "text/html"},
            request=request,
        )
    return _fixture_handler(request)


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
    assert not any(
        request.url.host == "www.londonstockexchange.com" for request in requests
    )
    assert any(
        request.method == "GET"
        and request.url.path == "/api/v1/pages"
        and request.url.params.get("path") == "reports"
        for request in requests
    )
    posted = [
        request
        for request in requests
        if request.method == "POST" and request.url.path == "/api/v1/components/refresh"
    ]
    assert len(posted) == 1
    body = json.loads(posted[0].content)
    assert body == {
        "path": "reports",
        "parameters": "tab=instruments&tabId=instrument-tab-id",
        "components": [
            {"componentId": "block_content:instrument-mod", "parameters": None}
        ],
    }
    assert any(request.url.path == _INSTRUMENT_LIST_PATH for request in requests)
    assert LSE_INSTRUMENT_LIST_CTA_TITLE not in "".join(
        str(request.url) for request in requests
    )


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


async def test_fresh_legacy_issuer_csv_is_refreshed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    version_id, version_dir = cache.begin_version(CacheSource.LSE_ISSUERS)
    (version_dir / "issuers_report.csv").write_text(
        "TIDM,Issuer Name,ISIN,Market,Instrument name,Sector\n"
        "AZN,AstraZeneca PLC,GB0009895292,MAIN MARKET,Ordinary Shares,Pharmaceuticals\n"
    )
    cache.publish(CacheSource.LSE_ISSUERS, version_id=version_id, record_count=1)
    assert cache.is_fresh(CacheSource.LSE_ISSUERS)
    requests = _install_mock_client(monkeypatch, _fixture_handler)

    page = await list_uk_listed_equities()

    assert {item.symbol for item in page.items} == set(EXPECTED_MARKETS)
    assert any(
        request.method == "GET" and request.url.path == "/api/v1/pages"
        for request in requests
    )


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

    with pytest.raises(SchemaValidationError, match="instrument-list header row"):
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


async def test_empty_cms_handshake_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    _install_mock_client(monkeypatch, _empty_cms_handler)

    with pytest.raises(SchemaValidationError, match="found 0"):
        await refresh_lse_issuers()


async def test_html_reports_page_is_not_used_for_discovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = RegulatoryDataCache(tmp_path)
    _bind_cache(monkeypatch, cache)
    requests = _install_mock_client(monkeypatch, _html_reports_page_handler)

    page = await refresh_lse_issuers()
    listed = await list_uk_listed_equities()

    assert page.record_count == len(EXPECTED_MARKETS)
    assert {item.symbol for item in listed.items} == set(EXPECTED_MARKETS)
    assert not any(request.url.path == "/reports" for request in requests)


def test_archive_cta_title_is_not_selected() -> None:
    url = lse_module._instrument_list_url(_REFRESH_JSON)
    assert url.endswith("/instrument-list.xlsx")
    assert "archive" not in url


def test_normalised_instrument_headers_are_accepted() -> None:
    rows = [
        ["tidm", "issuer name", "instrument name", "isin", "lse market"],
        ["AZN", "AstraZeneca PLC", "ORD USD0.25", "GB0009895292", "MAIN MARKET"],
    ]
    listings, skipped = lse_module._listings_from_rows(
        rows, source_refreshed_at=lse_module.utc_now()
    )
    assert skipped == 0
    assert [row.symbol for row in listings] == ["AZN"]
    assert listings[0].market == UkMarket.MAIN
    assert listings[0].isin == "GB0009895292"


def test_old_issuer_csv_headers_are_rejected() -> None:
    rows = [
        [
            "TIDM",
            "Issuer Name",
            "ISIN",
            "Market",
            "Instrument name",
            "Sector",
        ],
        [
            "AZN",
            "AstraZeneca PLC",
            "GB0009895292",
            "MAIN MARKET",
            "Ordinary Shares",
            "Pharmaceuticals",
        ],
    ]
    with pytest.raises(SchemaValidationError, match="instrument-list header row"):
        lse_module._listings_from_rows(rows, source_refreshed_at=lse_module.utc_now())
