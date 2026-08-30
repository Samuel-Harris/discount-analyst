import csv
from datetime import datetime
from pathlib import Path

from discount_analyst.agents.tools.regulatory_data.cache import (
    RegulatoryDataCache,
    ensure_fresh_snapshot,
)
from discount_analyst.agents.tools.regulatory_data.errors import (
    SchemaValidationError,
)
from discount_analyst.agents.tools.regulatory_data.exchanges.equity_classifier import (
    is_excluded_security_name,
)
from discount_analyst.agents.tools.regulatory_data.http import (
    create_metadata_client,
    stream_url_to_path,
)
from discount_analyst.agents.tools.regulatory_data.models import (
    CacheSource,
    EquityListing,
    ListedEquitiesPage,
    SourceRefreshResult,
    UsExchange,
    utc_now,
)
from discount_analyst.agents.tools.regulatory_data.pagination import (
    DEFAULT_PAGE_LIMIT,
    page_listings,
)

NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"

NASDAQ_LISTED_HEADERS = (
    "Symbol",
    "Security Name",
    "Market Category",
    "Test Issue",
    "Financial Status",
    "Round Lot Size",
    "ETF",
    "NextShares",
)
OTHER_LISTED_HEADERS = (
    "ACT Symbol",
    "Security Name",
    "Exchange",
    "CQS Symbol",
    "ETF",
    "Round Lot Size",
    "Test Issue",
    "NASDAQ Symbol",
)

# NASDAQ Trader `otherlisted.txt` Exchange column.
OTHER_LISTED_EXCHANGE_CODES = {
    "A": "NYSE American",
    "N": "NYSE",
}

NASDAQ_MARKET_CATEGORY = {
    "Q": "NASDAQ GS",
    "G": "NASDAQ GM",
    "S": "NASDAQ CM",
}

_NASDAQ_LISTED_FILENAME = "nasdaqlisted.txt"
_OTHER_LISTED_FILENAME = "otherlisted.txt"
_FILE_CREATION_PREFIX = "File Creation Time:"
_SOURCE = CacheSource.NASDAQ_TRADER


async def list_us_listed_equities(
    exchange: str | None = None,
    symbol_prefix: str | None = None,
    name_contains: str | None = None,
    limit: int = DEFAULT_PAGE_LIMIT,
    cursor: str | None = None,
) -> ListedEquitiesPage:
    """List currently listed US equities from the NASDAQ Trader symbol directory.

    Returns a paged snapshot of NASDAQ, NYSE, and NYSE American common equities.
    Test issues, ETFs, warrants, rights, units, preferred shares, notes, bonds,
    and funds are excluded. Default page size is 50 and the maximum is 100.

    Args:
        exchange: Optional exchange filter: ``NASDAQ``, ``NYSE``, or
            ``NYSE American``. Case is ignored. Omit to include all three.
        symbol_prefix: Optional case-insensitive ticker prefix (for example
            ``AA``).
        name_contains: Optional case-insensitive issuer-name substring.
        limit: Page size. Defaults to 50 and is capped at 100.
        cursor: Opaque pagination cursor from a previous ``next_cursor``. Omit
            to start at the first page.

    Returns:
        Matching listings plus ``total_count`` and ``next_cursor``.
    """
    cache = RegulatoryDataCache.from_settings()
    listings = await _load_listings(cache)
    return page_listings(
        listings,
        exchange=exchange,
        symbol_prefix=symbol_prefix,
        name_contains=name_contains,
        limit=limit,
        cursor=cursor,
    )


async def refresh_nasdaq_trader() -> SourceRefreshResult:
    cache = RegulatoryDataCache.from_settings()
    with cache.publishing(_SOURCE) as (version_dir, publish):
        async with create_metadata_client() as client:
            await stream_url_to_path(
                client, NASDAQ_LISTED_URL, version_dir / _NASDAQ_LISTED_FILENAME
            )
            await stream_url_to_path(
                client, OTHER_LISTED_URL, version_dir / _OTHER_LISTED_FILENAME
            )
        listings, skipped_count, file_creation_time = _parse_snapshot(
            version_dir, source_refreshed_at=utc_now()
        )
        snapshot = publish(
            record_count=len(listings),
            downloaded_version_or_date=file_creation_time,
        )
    return SourceRefreshResult(
        source=_SOURCE,
        version_id=snapshot.version_id,
        downloaded_version_or_date=snapshot.downloaded_version_or_date,
        record_count=snapshot.record_count,
        cache_path=str(version_dir),
        skipped_or_idempotent_count=skipped_count,
        active_snapshot=snapshot.relative_path,
    )


async def _load_listings(cache: RegulatoryDataCache) -> list[EquityListing]:
    snapshot, active_dir = await ensure_fresh_snapshot(
        cache, _SOURCE, refresh_nasdaq_trader, refresh_flags="--exchanges"
    )
    listings, _, _ = _parse_snapshot(
        active_dir, source_refreshed_at=snapshot.refreshed_at
    )
    return listings


def _parse_snapshot(
    version_dir: Path, *, source_refreshed_at: datetime
) -> tuple[list[EquityListing], int, str]:
    nasdaq_rows, nasdaq_creation = _read_pipe_table(
        version_dir / _NASDAQ_LISTED_FILENAME,
        NASDAQ_LISTED_HEADERS,
    )
    other_rows, other_creation = _read_pipe_table(
        version_dir / _OTHER_LISTED_FILENAME,
        OTHER_LISTED_HEADERS,
    )
    listings: list[EquityListing] = []
    skipped_count = 0
    for row in nasdaq_rows:
        listing = _listing_from_nasdaq_listed(row, source_refreshed_at)
        if listing is None:
            skipped_count += 1
            continue
        listings.append(listing)
    for row in other_rows:
        listing = _listing_from_other_listed(row, source_refreshed_at)
        if listing is None:
            skipped_count += 1
            continue
        listings.append(listing)
    return listings, skipped_count, nasdaq_creation or other_creation


def _read_pipe_table(
    path: Path, expected_headers: tuple[str, ...]
) -> tuple[list[dict[str, str]], str]:
    if not path.is_file():
        raise SchemaValidationError(
            _SOURCE, f"{path.name} is missing from the snapshot"
        )
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="|")
        try:
            header = next(reader)
        except StopIteration as exc:
            raise SchemaValidationError(_SOURCE, f"{path.name} is empty") from exc
        if tuple(header) != expected_headers:
            raise SchemaValidationError(
                _SOURCE,
                f"{path.name} header was {header!r}, expected {list(expected_headers)!r}",
            )
        records: list[dict[str, str]] = []
        file_creation_time = ""
        for row in reader:
            if not row or all(not cell.strip() for cell in row):
                continue
            first_cell = row[0].strip()
            if first_cell.startswith(_FILE_CREATION_PREFIX):
                file_creation_time = first_cell.removeprefix(
                    _FILE_CREATION_PREFIX
                ).strip()
                continue
            if len(row) != len(expected_headers):
                continue
            records.append(dict(zip(expected_headers, row, strict=True)))
    return records, file_creation_time


def _listing_from_nasdaq_listed(
    row: dict[str, str], source_refreshed_at: datetime
) -> EquityListing | None:
    if (
        _flag_is_yes(row["Test Issue"])
        or _flag_is_yes(row["ETF"])
        or _flag_is_yes(row["NextShares"])
    ):
        return None
    security_name = row["Security Name"].strip()
    if not security_name or is_excluded_security_name(security_name):
        return None
    market = NASDAQ_MARKET_CATEGORY.get(row["Market Category"].strip())
    if market is None:
        return None
    symbol = row["Symbol"].strip()
    if not symbol:
        return None
    return EquityListing(
        symbol=symbol,
        issuer_name=security_name,
        exchange=UsExchange.NASDAQ,
        market=market,
        isin=None,
        source=_SOURCE,
        source_refreshed_at=source_refreshed_at,
    )


def _listing_from_other_listed(
    row: dict[str, str], source_refreshed_at: datetime
) -> EquityListing | None:
    if _flag_is_yes(row["Test Issue"]) or _flag_is_yes(row["ETF"]):
        return None
    security_name = row["Security Name"].strip()
    if not security_name or is_excluded_security_name(security_name):
        return None
    mapped_exchange = OTHER_LISTED_EXCHANGE_CODES.get(row["Exchange"].strip())
    if mapped_exchange is None:
        return None
    symbol = row["ACT Symbol"].strip()
    if not symbol:
        return None
    return EquityListing(
        symbol=symbol,
        issuer_name=security_name,
        exchange=mapped_exchange,
        market=mapped_exchange,
        isin=None,
        source=_SOURCE,
        source_refreshed_at=source_refreshed_at,
    )


def _flag_is_yes(value: str) -> bool:
    return value.strip().casefold() == "y"
