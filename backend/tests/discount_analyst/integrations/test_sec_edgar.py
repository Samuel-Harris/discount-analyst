from __future__ import annotations

import json
import os
import zipfile
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from shutil import copyfile

import httpx
import pytest

from discount_analyst.agents.tools.regulatory_data import http as regulatory_http
from discount_analyst.agents.tools.regulatory_data.cache import (
    TTL_SEC_COMPANYFACTS_LIVE,
    TTL_SEC_SUBMISSIONS,
    TTL_SEC_TICKERS,
    RegulatoryDataCache,
)
from discount_analyst.agents.tools.regulatory_data.errors import (
    ColdCacheError,
    SecUserAgentMissingError,
    UnknownTickerError,
)
from discount_analyst.agents.tools.regulatory_data.models import CacheSource
from discount_analyst.agents.tools.regulatory_data.sec_edgar.company_facts import (
    SEC_COMPANYFACTS_API_URL,
    SEC_COMPANYFACTS_ZIP_URL,
    SEC_COMPANY_TICKERS_URL,
    SEC_SUBMISSIONS_API_URL,
    get_sec_company_facts,
    refresh_sec_edgar,
)
from discount_analyst.config.testing_settings import dashboard_settings_for_tests

SEC_FIXTURE_DIR = (
    Path(__file__).resolve().parents[2] / "fixtures" / "regulatory_data" / "sec"
)
TICKERS_FIXTURE = SEC_FIXTURE_DIR / "company_tickers.json"
COMPANYFACTS_FIXTURE = SEC_FIXTURE_DIR / "companyfacts_cik_0000320193.json"
SUBMISSIONS_FIXTURE = SEC_FIXTURE_DIR / "submissions_cik_0000320193.json"

TEST_USER_AGENT = "DiscountAnalyst/0.1 (a@b.com)"
AAPL_CIK = "0000320193"
AMENDMENT_REVENUE = Decimal("383000000000")
AMENDMENT_NET_INCOME = Decimal("97000000000")
ORIGINAL_10K_REVENUE = Decimal("383285000000")
ORIGINAL_10K_NET_INCOME = Decimal("96995000000")
FY2023_DEBT_TOTAL = Decimal("106530000000")
Q3_REVENUE = Decimal("85777000000")
Q3_DEBT_SUM = Decimal("100000000000")
FY2023_ASSETS = Decimal("352583000000")
Q3_ASSETS = Decimal("331612000000")


def _configure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    sec_user_agent: str = TEST_USER_AGENT,
) -> RegulatoryDataCache:
    settings = dashboard_settings_for_tests(
        sec_user_agent=sec_user_agent,
        regulatory_data_cache_dir=tmp_path,
    )
    monkeypatch.setattr(regulatory_http, "app_settings", settings)

    def _from_settings(cls: type[RegulatoryDataCache]) -> RegulatoryDataCache:
        return RegulatoryDataCache(tmp_path)

    monkeypatch.setattr(
        RegulatoryDataCache, "from_settings", classmethod(_from_settings)
    )
    return RegulatoryDataCache(tmp_path)


def _install_mock_http(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[[httpx.Request], httpx.Response],
) -> list[httpx.Request]:
    requests: list[httpx.Request] = []

    def transport_handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    def fake_client(*, timeout: float | None = None) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(transport_handler))

    monkeypatch.setattr(regulatory_http, "create_metadata_client", fake_client)
    monkeypatch.setattr(regulatory_http, "create_bulk_client", fake_client)
    return requests


def _fixture_handler(
    *,
    tickers: bool = True,
    companyfacts: bool = True,
    submissions: bool = True,
    zip_bytes: bytes | None = None,
) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == SEC_COMPANY_TICKERS_URL:
            if not tickers:
                return httpx.Response(404, request=request)
            return httpx.Response(
                200, content=TICKERS_FIXTURE.read_bytes(), request=request
            )
        if url == SEC_COMPANYFACTS_API_URL.format(cik=AAPL_CIK):
            if not companyfacts:
                return httpx.Response(404, request=request)
            return httpx.Response(
                200, content=COMPANYFACTS_FIXTURE.read_bytes(), request=request
            )
        if url == SEC_SUBMISSIONS_API_URL.format(cik=AAPL_CIK):
            if not submissions:
                return httpx.Response(404, request=request)
            return httpx.Response(
                200, content=SUBMISSIONS_FIXTURE.read_bytes(), request=request
            )
        if url == SEC_COMPANYFACTS_ZIP_URL:
            if zip_bytes is None:
                return httpx.Response(404, request=request)
            return httpx.Response(200, content=zip_bytes, request=request)
        return httpx.Response(404, request=request)

    return handler


def _seed_tickers(cache: RegulatoryDataCache) -> None:
    dest = cache.ttl_file(TTL_SEC_TICKERS, "company_tickers.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(TICKERS_FIXTURE.read_bytes())


def _seed_companyfacts(cache: RegulatoryDataCache) -> None:
    version_id, version_dir = cache.begin_version(CacheSource.SEC_COMPANYFACTS)
    copyfile(COMPANYFACTS_FIXTURE, version_dir / f"CIK{AAPL_CIK}.json")
    cache.publish(CacheSource.SEC_COMPANYFACTS, version_id=version_id, record_count=1)


def _seed_submissions(cache: RegulatoryDataCache) -> None:
    dest = cache.ttl_file(TTL_SEC_SUBMISSIONS, f"CIK{AAPL_CIK}.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(SUBMISSIONS_FIXTURE.read_bytes())


def _seed_local_snapshot(cache: RegulatoryDataCache) -> None:
    _seed_tickers(cache)
    _seed_companyfacts(cache)
    _seed_submissions(cache)


def _tiny_companyfacts_zip(tmp_path: Path) -> bytes:
    zip_path = tmp_path / "companyfacts-tiny.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(f"CIK{AAPL_CIK}.json", COMPANYFACTS_FIXTURE.read_bytes())
    return zip_path.read_bytes()


def _forbid_network(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"unexpected SEC request: {request.url}")


async def test_missing_user_agent_blocks_refresh(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _configure(monkeypatch, tmp_path, sec_user_agent="")
    _install_mock_http(monkeypatch, _forbid_network)
    with pytest.raises(SecUserAgentMissingError, match="SEC__USER_AGENT"):
        await refresh_sec_edgar()


async def test_missing_user_agent_blocks_gap_fill(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path, sec_user_agent="")
    _seed_tickers(cache)
    _install_mock_http(monkeypatch, _forbid_network)
    with pytest.raises(SecUserAgentMissingError, match="SEC__USER_AGENT"):
        await get_sec_company_facts("AAPL")


async def test_user_agent_sent_on_sec_requests(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _configure(monkeypatch, tmp_path)
    requests = _install_mock_http(monkeypatch, _fixture_handler())
    snapshot = await get_sec_company_facts("AAPL")
    assert snapshot.cik == AAPL_CIK
    assert requests
    for request in requests:
        assert request.headers["User-Agent"] == TEST_USER_AGENT
        assert SEC_COMPANYFACTS_ZIP_URL not in str(request.url)


async def test_ticker_maps_to_padded_cik(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_local_snapshot(cache)
    _install_mock_http(monkeypatch, _forbid_network)
    snapshot = await get_sec_company_facts("  aapl  ")
    assert snapshot.identifier == "AAPL"
    assert snapshot.cik == AAPL_CIK
    assert snapshot.issuer_name == "Apple Inc."
    assert snapshot.company_number is None
    assert snapshot.accounts_filleted is None


async def test_stale_ticker_file_is_served_when_refresh_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_local_snapshot(cache)
    tickers_path = cache.ttl_file(TTL_SEC_TICKERS, "company_tickers.json")
    aged = (datetime.now(tz=UTC) - timedelta(hours=25)).timestamp()
    os.utime(tickers_path, (aged, aged))
    _install_mock_http(monkeypatch, _forbid_network)
    snapshot = await get_sec_company_facts("AAPL")
    assert snapshot.cik == AAPL_CIK
    assert snapshot.revenue == AMENDMENT_REVENUE


async def test_unknown_ticker_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_tickers(cache)
    _install_mock_http(monkeypatch, _forbid_network)
    with pytest.raises(UnknownTickerError, match="NOPE"):
        await get_sec_company_facts("NOPE")


async def test_annual_amendment_wins_for_latest_filing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_local_snapshot(cache)
    _install_mock_http(monkeypatch, _forbid_network)
    snapshot = await get_sec_company_facts("AAPL")
    assert snapshot.period_kind == "annual"
    assert snapshot.period_end == date(2023, 9, 30)
    assert snapshot.form_type == "10-K/A"
    assert snapshot.filed_at == date(2023, 12, 15)
    assert snapshot.revenue == AMENDMENT_REVENUE
    assert snapshot.net_income == AMENDMENT_NET_INCOME
    assert snapshot.revenue != ORIGINAL_10K_REVENUE
    assert snapshot.profit_and_loss_available is True
    assert snapshot.currency == "USD"


async def test_as_of_selects_original_10k_before_amendment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_local_snapshot(cache)
    _install_mock_http(monkeypatch, _forbid_network)
    snapshot = await get_sec_company_facts("AAPL", as_of=date(2023, 11, 10))
    assert snapshot.form_type == "10-K"
    assert snapshot.filed_at == date(2023, 11, 3)
    assert snapshot.period_end == date(2023, 9, 30)
    assert snapshot.revenue == ORIGINAL_10K_REVENUE
    assert snapshot.net_income == ORIGINAL_10K_NET_INCOME


async def test_quarterly_selects_latest_10q(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_local_snapshot(cache)
    _install_mock_http(monkeypatch, _forbid_network)
    snapshot = await get_sec_company_facts("AAPL", period_kind="quarterly")
    assert snapshot.form_type == "10-Q"
    assert snapshot.period_end == date(2024, 6, 29)
    assert snapshot.revenue == Q3_REVENUE


async def test_same_period_does_not_mix_annual_and_quarterly(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_local_snapshot(cache)
    _install_mock_http(monkeypatch, _forbid_network)
    quarterly = await get_sec_company_facts("AAPL", period_kind="quarterly")
    annual = await get_sec_company_facts("AAPL", as_of=date(2023, 11, 10))
    assert quarterly.revenue == Q3_REVENUE
    assert quarterly.total_assets == Q3_ASSETS
    assert quarterly.total_assets != FY2023_ASSETS
    assert annual.revenue == ORIGINAL_10K_REVENUE
    assert annual.total_assets == FY2023_ASSETS
    assert annual.total_assets != Q3_ASSETS


async def test_debt_uses_total_not_sum_of_components_for_annual(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_local_snapshot(cache)
    _install_mock_http(monkeypatch, _forbid_network)
    snapshot = await get_sec_company_facts("AAPL", as_of=date(2023, 11, 10))
    assert snapshot.debt == FY2023_DEBT_TOTAL
    assert snapshot.debt != Decimal("105103000000")


async def test_debt_sums_components_when_no_total(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_local_snapshot(cache)
    _install_mock_http(monkeypatch, _forbid_network)
    snapshot = await get_sec_company_facts("AAPL", period_kind="quarterly")
    assert snapshot.debt == Q3_DEBT_SUM


async def test_cash_is_explicitly_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_local_snapshot(cache)
    _install_mock_http(monkeypatch, _forbid_network)
    snapshot = await get_sec_company_facts("AAPL", as_of=date(2023, 11, 10))
    assert snapshot.cash is None
    assert "cash" in snapshot.missing_fields


async def test_submissions_handles_are_newest_first_and_well_formed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_local_snapshot(cache)
    _install_mock_http(monkeypatch, _forbid_network)
    snapshot = await get_sec_company_facts("AAPL")
    assert len(snapshot.recent_filings) == 5
    forms = [handle.form_type for handle in snapshot.recent_filings]
    assert "8-K" not in forms
    assert forms[0] == "10-Q"
    first = snapshot.recent_filings[0]
    assert first.period_end == date(2024, 6, 29)
    assert first.accession_or_document_id == "0000320193-24-000069"
    assert first.source_url == (
        "https://www.sec.gov/Archives/edgar/data/320193/"
        "000032019324000069/aapl-20240629.htm"
    )
    filed_dates = [handle.filed_at for handle in snapshot.recent_filings]
    assert filed_dates == sorted(filed_dates, reverse=True)


async def test_unavailable_submissions_leave_empty_handles(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_tickers(cache)
    _seed_companyfacts(cache)
    _install_mock_http(monkeypatch, _fixture_handler(submissions=False))
    snapshot = await get_sec_company_facts("AAPL")
    assert snapshot.revenue == AMENDMENT_REVENUE
    assert snapshot.recent_filings == []


async def test_cold_cache_gap_fill_is_write_through(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_tickers(cache)
    requests = _install_mock_http(monkeypatch, _fixture_handler())
    snapshot = await get_sec_company_facts("AAPL")
    assert snapshot.revenue == AMENDMENT_REVENUE
    cached = cache.ttl_file(TTL_SEC_COMPANYFACTS_LIVE, f"CIK{AAPL_CIK}.json")
    assert cached.is_file()
    assert json.loads(cached.read_text())["entityName"] == "Apple Inc."
    assert cache.active_dir(CacheSource.SEC_COMPANYFACTS) is None
    facts_urls = [
        str(request.url)
        for request in requests
        if str(request.url) == SEC_COMPANYFACTS_API_URL.format(cik=AAPL_CIK)
    ]
    assert len(facts_urls) == 1
    assert SEC_COMPANYFACTS_ZIP_URL not in {str(request.url) for request in requests}

    requests.clear()
    again = await get_sec_company_facts("AAPL")
    assert again.revenue == AMENDMENT_REVENUE
    assert SEC_COMPANYFACTS_API_URL.format(cik=AAPL_CIK) not in {
        str(request.url) for request in requests
    }


async def test_gap_fill_without_facts_raises_cold_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    _seed_tickers(cache)
    _install_mock_http(monkeypatch, _fixture_handler(companyfacts=False))
    with pytest.raises(ColdCacheError, match="refresh-regulatory-data --sec"):
        await get_sec_company_facts("AAPL")


async def test_refresh_from_tiny_zip_publishes_snapshot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = _configure(monkeypatch, tmp_path)
    zip_bytes = _tiny_companyfacts_zip(tmp_path)
    _install_mock_http(monkeypatch, _fixture_handler(zip_bytes=zip_bytes))
    first = await refresh_sec_edgar()
    assert first.source == CacheSource.SEC_COMPANYFACTS.value
    assert first.record_count == 1
    active = cache.active_dir(CacheSource.SEC_COMPANYFACTS)
    assert active is not None
    assert (active / f"CIK{AAPL_CIK}.json").is_file()
    second = await refresh_sec_edgar()
    assert second.record_count == 1
    assert second.version_id != first.version_id
    latest = cache.active_dir(CacheSource.SEC_COMPANYFACTS)
    assert latest is not None
    assert (latest / f"CIK{AAPL_CIK}.json").is_file()
