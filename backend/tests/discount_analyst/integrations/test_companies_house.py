from shutil import copyfile
from datetime import date
from decimal import Decimal
from pathlib import Path
import zipfile

import httpx
import pytest

from discount_analyst.agents.tools.regulatory_data.cache import RegulatoryDataCache
from discount_analyst.agents.tools.regulatory_data.companies_house import (
    accounts as accounts_module,
)
from discount_analyst.agents.tools.regulatory_data.companies_house.accounts import (
    get_companies_house_accounts,
    refresh_companies_house,
)
from discount_analyst.agents.tools.regulatory_data.companies_house.ingest import (
    ingest_account_ixbrl,
    ingest_companies_csv,
    select_company_data_href,
    select_daily_archive_hrefs,
    select_monthly_archive_hrefs,
    zip_hrefs_from_html,
)
from discount_analyst.agents.tools.regulatory_data.companies_house.resolve import (
    resolve_uk_company,
)
from discount_analyst.agents.tools.regulatory_data.companies_house.store import (
    SQLITE_FILENAME,
    account_count,
    initialise_database,
    require_active_database,
)
from discount_analyst.agents.tools.regulatory_data.errors import (
    REFRESH_COMMAND,
    ColdCacheError,
    SchemaValidationError,
)
from discount_analyst.agents.tools.regulatory_data.models import CacheSource

FIXTURE_DIR = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "regulatory_data"
    / "companies_house"
)
COMPANIES_CSV = FIXTURE_DIR / "companies.csv"
IFRS_XHTML = FIXTURE_DIR / "accounts_ifrs.xhtml"
COMPARATIVE_XHTML = FIXTURE_DIR / "accounts_ifrs_comparative.xhtml"
FILLETED_XHTML = FIXTURE_DIR / "accounts_ukgaap_filleted.xhtml"
COMPANIES_INDEX = FIXTURE_DIR / "companies_index.html"
MONTHLY_INDEX = FIXTURE_DIR / "monthly_index.html"
DAILY_INDEX = FIXTURE_DIR / "daily_index.html"
LSE_ISSUERS_REPORT = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "regulatory_data"
    / "lse"
    / "issuers_report.csv"
)

AZN_NUMBER = "02723534"
AZN_NAME = "ASTRAZENECA PLC"


@pytest.fixture
def cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> RegulatoryDataCache:
    cache = RegulatoryDataCache(tmp_path)

    def from_settings(cls: type[RegulatoryDataCache]) -> RegulatoryDataCache:
        return cache

    monkeypatch.setattr(
        RegulatoryDataCache, "from_settings", classmethod(from_settings)
    )
    return cache


def _publish_seed(
    cache: RegulatoryDataCache,
    *,
    accounts: list[tuple[str, date, date, Path, str]] | None = None,
) -> Path:
    version_id, version_dir = cache.begin_version(CacheSource.COMPANIES_HOUSE)
    connection = initialise_database(version_dir)
    ingest_companies_csv(connection, COMPANIES_CSV)
    for company_number, filed_at, period_end, path, source_id in accounts or []:
        ingest_account_ixbrl(
            connection, company_number, filed_at, period_end, path, source_id
        )
    records = 5 + (0 if accounts is None else len(accounts))
    connection.close()
    cache.publish(
        CacheSource.COMPANIES_HOUSE,
        version_id=version_id,
        record_count=records,
    )
    return version_dir


def _publish_lse(cache: RegulatoryDataCache) -> None:
    version_id, version_dir = cache.begin_version(CacheSource.LSE_ISSUERS)
    copyfile(LSE_ISSUERS_REPORT, version_dir / "issuers_report.csv")
    cache.publish(CacheSource.LSE_ISSUERS, version_id=version_id, record_count=5)


def _write_zip(path: Path, inner_name: str, data: bytes) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(inner_name, data)


def test_idempotent_account_ingest(tmp_path: Path) -> None:
    connection = initialise_database(tmp_path)
    ingest_companies_csv(connection, COMPANIES_CSV)
    first = ingest_account_ixbrl(
        connection,
        AZN_NUMBER,
        date(2024, 3, 1),
        date(2023, 12, 31),
        IFRS_XHTML,
        "azn-2023.html",
    )
    second = ingest_account_ixbrl(
        connection,
        AZN_NUMBER,
        date(2024, 3, 1),
        date(2023, 12, 31),
        IFRS_XHTML,
        "azn-2023.html",
    )
    assert first.inserted_count == 1
    assert first.skipped_or_idempotent_count == 0
    assert second.inserted_count == 0
    assert second.skipped_or_idempotent_count >= 1
    assert account_count(connection) == 1
    connection.close()


async def test_exact_resolver_name_and_number(cache: RegulatoryDataCache) -> None:
    _publish_seed(cache)
    by_name = await resolve_uk_company("ASTRAZENECA PLC")
    assert by_name.selected is not None
    assert by_name.selected.company_number == AZN_NUMBER
    assert by_name.selected.company_name == AZN_NAME
    by_number = await resolve_uk_company("02723534")
    assert by_number.selected is not None
    assert by_number.selected.company_number == AZN_NUMBER
    padded = await resolve_uk_company("2723534")
    assert padded.selected is not None
    assert padded.selected.company_number == AZN_NUMBER


async def test_ambiguous_name_is_not_auto_selected(
    cache: RegulatoryDataCache,
) -> None:
    _publish_seed(cache)
    partial = await resolve_uk_company("AMBIGUOUS EXAMPLE")
    assert partial.selected is None
    assert partial.candidates == []
    exact = await resolve_uk_company("AMBIGUOUS EXAMPLE LTD")
    assert exact.selected is not None
    assert exact.selected.company_number == "12345678"
    assert exact.selected.company_name == "AMBIGUOUS EXAMPLE LTD"


async def test_tidm_resolves_via_cached_lse_snapshot(
    cache: RegulatoryDataCache,
) -> None:
    _publish_seed(cache)
    _publish_lse(cache)
    by_tidm = await resolve_uk_company("AZN")
    assert by_tidm.selected is not None
    assert by_tidm.selected.company_number == AZN_NUMBER
    dotted = await resolve_uk_company("azn.l")
    assert dotted.selected is not None
    assert dotted.selected.company_number == AZN_NUMBER


async def test_tidm_is_unresolved_without_lse_snapshot(
    cache: RegulatoryDataCache,
) -> None:
    _publish_seed(cache)
    result = await resolve_uk_company("AZN")
    assert result.selected is None
    assert result.candidates == []


async def test_comparative_ixbrl_uses_latest_period(
    cache: RegulatoryDataCache,
) -> None:
    _publish_seed(
        cache,
        accounts=[
            (
                AZN_NUMBER,
                date(2024, 3, 1),
                date(2023, 12, 31),
                COMPARATIVE_XHTML,
                "azn-comparative.html",
            )
        ],
    )
    snapshot = await get_companies_house_accounts(AZN_NUMBER)
    assert snapshot.revenue == Decimal("44738000000")
    assert snapshot.net_income == Decimal("5960000000")
    assert snapshot.currency == "GBP"
    assert snapshot.issuer_name == AZN_NAME


async def test_ifrs_mappings(cache: RegulatoryDataCache) -> None:
    _publish_seed(
        cache,
        accounts=[
            (
                AZN_NUMBER,
                date(2024, 3, 1),
                date(2023, 12, 31),
                IFRS_XHTML,
                "azn-2023.html",
            )
        ],
    )
    snapshot = await get_companies_house_accounts(AZN_NUMBER)
    assert snapshot.identifier == AZN_NUMBER
    assert snapshot.cik is None
    assert snapshot.company_number == AZN_NUMBER
    assert snapshot.issuer_name == AZN_NAME
    assert snapshot.currency == "GBP"
    assert snapshot.period_kind == "annual"
    assert snapshot.period_end == date(2023, 12, 31)
    assert snapshot.filed_at == date(2024, 3, 1)
    assert snapshot.revenue == Decimal("44738000000")
    assert snapshot.net_income == Decimal("5960000000")
    assert snapshot.total_assets == Decimal("101119000000")
    assert snapshot.total_liabilities == Decimal("59607000000")
    assert snapshot.equity == Decimal("41512000000")
    assert snapshot.cash == Decimal("5894000000")
    assert snapshot.debt == Decimal("22845000000")
    assert snapshot.accounts_filleted is False
    assert snapshot.profit_and_loss_available is True


async def test_as_of_selects_older_period(cache: RegulatoryDataCache) -> None:
    _publish_seed(
        cache,
        accounts=[
            (
                AZN_NUMBER,
                date(2024, 3, 1),
                date(2023, 12, 31),
                IFRS_XHTML,
                "azn-2023.html",
            ),
            (
                AZN_NUMBER,
                date(2025, 3, 1),
                date(2024, 12, 31),
                IFRS_XHTML,
                "azn-2024.html",
            ),
        ],
    )
    older = await get_companies_house_accounts(AZN_NUMBER, as_of=date(2024, 6, 1))
    assert older.filed_at == date(2024, 3, 1)
    assert older.period_end == date(2023, 12, 31)
    latest = await get_companies_house_accounts(AZN_NUMBER)
    assert latest.filed_at == date(2025, 3, 1)
    assert latest.period_end == date(2024, 12, 31)


async def test_filleted_account_marks_missing_profit_and_loss(
    cache: RegulatoryDataCache,
) -> None:
    _publish_seed(
        cache,
        accounts=[
            (
                "00526832",
                date(2024, 6, 1),
                date(2024, 3, 31),
                FILLETED_XHTML,
                "gooch-filleted.html",
            )
        ],
    )
    snapshot = await get_companies_house_accounts("00526832")
    assert snapshot.accounts_filleted is True
    assert snapshot.profit_and_loss_available is False
    assert snapshot.revenue is None
    assert snapshot.net_income is None
    assert snapshot.total_assets == Decimal("2140000")
    assert snapshot.total_liabilities == Decimal("500000")
    assert snapshot.equity == Decimal("1640000")
    assert snapshot.cash == Decimal("220000")
    assert "revenue" in snapshot.missing_fields
    assert "net_income" in snapshot.missing_fields


async def test_cold_cache_errors_name_refresh_command(
    cache: RegulatoryDataCache,
) -> None:
    with pytest.raises(ColdCacheError, match=REFRESH_COMMAND) as name_error:
        await resolve_uk_company(AZN_NAME)
    assert "--companies-house" in str(name_error.value)
    with pytest.raises(ColdCacheError, match=REFRESH_COMMAND) as accounts_error:
        await get_companies_house_accounts(AZN_NUMBER)
    assert "--companies-house" in str(accounts_error.value)
    assert "discount-analyst admin refresh-regulatory-data --companies-house" in str(
        accounts_error.value
    )


async def test_atomic_publish_rollback(
    cache: RegulatoryDataCache, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_dir = _publish_seed(cache)
    assert cache.active_dir(CacheSource.COMPANIES_HOUSE) == first_dir

    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("NotCompanyName,Foo\nbar,baz\n", encoding="utf-8")
    companies_zip = tmp_path / "BasicCompanyDataAsOneFile-2026-08-01.zip"
    _write_zip(companies_zip, "companies.csv", bad_csv.read_bytes())

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.endswith("en_output.html"):
            return httpx.Response(200, text=COMPANIES_INDEX.read_text())
        if url.endswith("en_monthlyaccountsdata.html"):
            return httpx.Response(200, text="<html><body></body></html>")
        if url.endswith("en_accountsdata.html"):
            return httpx.Response(200, text="<html><body></body></html>")
        if url.endswith("BasicCompanyDataAsOneFile-2026-08-01.zip"):
            return httpx.Response(200, content=companies_zip.read_bytes())
        return httpx.Response(404, text="missing")

    def fake_client() -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(accounts_module, "create_metadata_client", fake_client)
    monkeypatch.setattr(accounts_module, "create_bulk_client", fake_client)

    with pytest.raises(SchemaValidationError, match="missing headers"):
        await refresh_companies_house()

    assert cache.active_dir(CacheSource.COMPANIES_HOUSE) == first_dir
    assert cache.load_manifest().sources["companies_house"].version_id == first_dir.name
    assert (first_dir / SQLITE_FILENAME).is_file()
    require_active_database(cache)


def test_index_parsers_select_one_file_trailing_monthlies_and_newer_dailies() -> None:
    company_hrefs = zip_hrefs_from_html(COMPANIES_INDEX.read_text())
    assert select_company_data_href(company_hrefs) == (
        "BasicCompanyDataAsOneFile-2026-08-01.zip"
    )
    monthly_hrefs = zip_hrefs_from_html(MONTHLY_INDEX.read_text())
    monthly = select_monthly_archive_hrefs(monthly_hrefs)
    assert [Path(href).name for _, href in monthly] == [
        "Accounts_Monthly_Data-June2026.zip",
        "Accounts_Monthly_Data-July2026.zip",
    ]
    daily_hrefs = zip_hrefs_from_html(DAILY_INDEX.read_text())
    daily = select_daily_archive_hrefs(daily_hrefs, after=monthly[-1][0])
    assert [Path(href).name for _, href in daily] == [
        "Accounts_Bulk_Data-2026-08-15.zip"
    ]


def test_trailing_monthly_limit_is_eighteen() -> None:
    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    hrefs: list[str] = []
    for year in (2024, 2025, 2026):
        for name in month_names:
            hrefs.append(f"Accounts_Monthly_Data-{name}{year}.zip")
    selected = select_monthly_archive_hrefs(hrefs, limit=18)
    assert len(selected) == 18
    assert selected[0][0] == date(2025, 7, 31)
    assert selected[-1][0] == date(2026, 12, 31)


async def test_refresh_ingests_mocked_archives(
    cache: RegulatoryDataCache, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    companies_zip = tmp_path / "BasicCompanyDataAsOneFile-2026-08-01.zip"
    _write_zip(companies_zip, "companies.csv", COMPANIES_CSV.read_bytes())
    monthly_zip = tmp_path / "Accounts_Monthly_Data-July2026.zip"
    _write_zip(
        monthly_zip,
        "Prod223_0001_02723534_20231231.html",
        IFRS_XHTML.read_bytes(),
    )
    empty_monthly = tmp_path / "Accounts_Monthly_Data-June2026.zip"
    _write_zip(empty_monthly, "readme.txt", b"no accounts")
    daily_zip = tmp_path / "Accounts_Bulk_Data-2026-08-15.zip"
    _write_zip(
        daily_zip,
        "Prod223_0001_00526832_20240331.html",
        FILLETED_XHTML.read_bytes(),
    )
    payloads = {
        "en_output.html": COMPANIES_INDEX.read_text(),
        "en_monthlyaccountsdata.html": MONTHLY_INDEX.read_text(),
        "en_accountsdata.html": DAILY_INDEX.read_text(),
        "BasicCompanyDataAsOneFile-2026-08-01.zip": companies_zip.read_bytes(),
        "Accounts_Monthly_Data-July2026.zip": monthly_zip.read_bytes(),
        "Accounts_Monthly_Data-June2026.zip": empty_monthly.read_bytes(),
        "Accounts_Bulk_Data-2026-08-15.zip": daily_zip.read_bytes(),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        name = Path(str(request.url)).name
        if name in payloads:
            payload = payloads[name]
            if isinstance(payload, bytes):
                return httpx.Response(200, content=payload)
            return httpx.Response(200, text=payload)
        return httpx.Response(404, text=name)

    def fake_client() -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(accounts_module, "create_metadata_client", fake_client)
    monkeypatch.setattr(accounts_module, "create_bulk_client", fake_client)

    result = await refresh_companies_house()
    assert result.source == CacheSource.COMPANIES_HOUSE
    assert cache.active_dir(CacheSource.COMPANIES_HOUSE) is not None
    azn = await get_companies_house_accounts(AZN_NUMBER)
    assert azn.revenue == Decimal("44738000000")
    filleted = await get_companies_house_accounts("00526832")
    assert filleted.accounts_filleted is True


def test_invalid_company_csv_headers_are_rejected(tmp_path: Path) -> None:
    connection = initialise_database(tmp_path)
    bad = tmp_path / "bad.csv"
    bad.write_text("Nope,StillNope\n1,2\n", encoding="utf-8")
    with pytest.raises(SchemaValidationError, match="missing headers"):
        ingest_companies_csv(connection, bad)
    connection.close()
