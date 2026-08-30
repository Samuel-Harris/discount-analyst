from datetime import date
from pathlib import Path

from httpx import AsyncClient

from discount_analyst.agents.tools.regulatory_data.cache import RegulatoryDataCache
from discount_analyst.agents.tools.regulatory_data.companies_house.ingest import (
    COMPANIES_INDEX_URL,
    DAILY_ACCOUNTS_INDEX_URL,
    MONTHLY_ACCOUNTS_INDEX_URL,
    absolute_download_url,
    canonical_company_number,
    ingest_accounts_zip,
    ingest_companies_zip,
    select_company_data_href,
    select_daily_archive_hrefs,
    select_monthly_archive_hrefs,
    zip_hrefs_from_html,
)
from discount_analyst.agents.tools.regulatory_data.companies_house.store import (
    SQLITE_FILENAME,
    account_count,
    company_count,
    connect,
    decimal_from_text,
    fetch_account_as_of,
    fetch_company_by_number,
    initialise_database,
    require_active_database,
    validate_database,
)
from discount_analyst.agents.tools.regulatory_data.errors import (
    REFRESH_COMMAND,
    RegulatoryDataError,
    SchemaValidationError,
)
from discount_analyst.agents.tools.regulatory_data.http import (
    create_bulk_client,
    create_metadata_client,
    stream_url_to_path,
)
from discount_analyst.agents.tools.regulatory_data.models import (
    CacheSource,
    CanonicalFundamentals,
    SourceRefreshResult,
    missing_fundamental_fields,
)

_SOURCE = CacheSource.COMPANIES_HOUSE


async def get_companies_house_accounts(
    company_number: str,
    as_of: date | None = None,
) -> CanonicalFundamentals:
    """Return the latest cached Companies House accounts on or before ``as_of``.

    Filleted accounts (no revenue and no profit) set ``accounts_filleted`` and
    leave P&L fields ``None``. Missing balance-sheet fields stay ``None`` and
    are listed in ``missing_fields``; they are never inferred as zero.

    Args:
        company_number: Companies House company number, including leading zeros.
        as_of: Inclusive filing-date cutoff. Omit to use the latest cached
            account for the company.

    Returns:
        One canonical fundamentals snapshot from the selected iXBRL filing.
    """
    cache = RegulatoryDataCache.from_settings()
    connection = connect(require_active_database(cache))
    try:
        number = canonical_company_number(company_number) or company_number.strip()
        row = fetch_account_as_of(connection, number, as_of)
        if row is None:
            cutoff = as_of.isoformat() if as_of is not None else "latest"
            raise RegulatoryDataError(
                f"No cached Companies House accounts for {number!r} "
                f"on or before {cutoff}. Run `{REFRESH_COMMAND} --companies-house` "
                "to download official bulk data."
            )
        company = fetch_company_by_number(connection, number)
        issuer_name = row["issuer_name"] or (
            company["company_name"] if company is not None else number
        )
        revenue = decimal_from_text(row["revenue"])
        net_income = decimal_from_text(row["net_income"])
        total_assets = decimal_from_text(row["total_assets"])
        total_liabilities = decimal_from_text(row["total_liabilities"])
        equity = decimal_from_text(row["equity"])
        cash = decimal_from_text(row["cash"])
        debt = decimal_from_text(row["debt"])
        shares_outstanding = decimal_from_text(row["shares_outstanding"])
        return CanonicalFundamentals(
            identifier=number,
            issuer_name=issuer_name,
            cik=None,
            company_number=number,
            currency=row["currency"],
            period_kind="annual",
            period_end=date.fromisoformat(row["period_end"]),
            filed_at=date.fromisoformat(row["filed_at"]),
            form_type=None,
            revenue=revenue,
            net_income=net_income,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            equity=equity,
            cash=cash,
            debt=debt,
            shares_outstanding=shares_outstanding,
            accounts_filleted=bool(row["accounts_filleted"]),
            profit_and_loss_available=bool(row["profit_and_loss_available"]),
            missing_fields=missing_fundamental_fields(
                revenue=revenue,
                net_income=net_income,
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                equity=equity,
                cash=cash,
                debt=debt,
                shares_outstanding=shares_outstanding,
            ),
        )
    finally:
        connection.close()


async def refresh_companies_house() -> SourceRefreshResult:
    cache = RegulatoryDataCache.from_settings()
    with cache.publishing(_SOURCE) as (version_dir, publish):
        skipped = await _download_and_ingest(version_dir)
        connection = connect(version_dir / SQLITE_FILENAME)
        try:
            validate_database(connection)
            records = company_count(connection) + account_count(connection)
        finally:
            connection.close()
        snapshot = publish(record_count=records)
        sqlite_path = version_dir / SQLITE_FILENAME
    return SourceRefreshResult(
        source=_SOURCE,
        version_id=snapshot.version_id,
        downloaded_version_or_date=snapshot.downloaded_version_or_date,
        record_count=records,
        cache_path=str(sqlite_path),
        skipped_or_idempotent_count=skipped,
        active_snapshot=snapshot.relative_path,
    )


async def _download_and_ingest(version_dir: Path) -> int:
    connection = initialise_database(version_dir)
    skipped = 0
    try:
        async with create_metadata_client() as metadata:
            companies_html = await _get_text(metadata, COMPANIES_INDEX_URL)
            monthly_html = await _get_text(metadata, MONTHLY_ACCOUNTS_INDEX_URL)
            daily_html = await _get_text(metadata, DAILY_ACCOUNTS_INDEX_URL)

        company_href = select_company_data_href(zip_hrefs_from_html(companies_html))
        if company_href is None:
            raise SchemaValidationError(
                "Companies House",
                "company data product zip was not listed on the index page",
            )
        company_url = absolute_download_url(COMPANIES_INDEX_URL, company_href)
        monthly = select_monthly_archive_hrefs(zip_hrefs_from_html(monthly_html))
        latest_monthly = monthly[-1][0] if monthly else None
        daily = select_daily_archive_hrefs(
            zip_hrefs_from_html(daily_html), after=latest_monthly
        )
        account_archives = [
            *(
                (filed_at, href, MONTHLY_ACCOUNTS_INDEX_URL)
                for filed_at, href in monthly
            ),
            *((filed_at, href, DAILY_ACCOUNTS_INDEX_URL) for filed_at, href in daily),
        ]

        downloads = version_dir / "downloads"
        downloads.mkdir(parents=True, exist_ok=True)
        async with create_bulk_client() as bulk:
            company_zip = downloads / Path(company_url).name
            await stream_url_to_path(bulk, company_url, company_zip)
            ingest_companies_zip(connection, company_zip)

            for filed_at, href, index_url in account_archives:
                url = absolute_download_url(index_url, href)
                archive_path = downloads / Path(url).name
                await stream_url_to_path(bulk, url, archive_path)
                result = ingest_accounts_zip(
                    connection,
                    archive_path,
                    filed_at=filed_at,
                    source_prefix=archive_path.name,
                )
                skipped += result.skipped_or_idempotent_count
        return skipped
    finally:
        connection.close()


async def _get_text(client: AsyncClient, url: str) -> str:
    response = await client.get(url)
    response.raise_for_status()
    return response.text
