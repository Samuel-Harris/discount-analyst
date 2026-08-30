import csv
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from lxml import etree, html

from discount_analyst.agents.tools.regulatory_data.cache import (
    RegulatoryDataCache,
    ensure_fresh_snapshot,
)
from discount_analyst.agents.tools.regulatory_data.errors import (
    SchemaValidationError,
)
from discount_analyst.agents.tools.regulatory_data.exchanges.equity_classifier import (
    is_excluded_security_name,
    is_ordinary_equity_instrument,
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
    UkMarket,
    utc_now,
)
from discount_analyst.agents.tools.regulatory_data.pagination import (
    DEFAULT_PAGE_LIMIT,
    page_listings,
)

LSE_REPORTS_URL = "https://www.londonstockexchange.com/reports?tab=issuers"
LSE_ISSUERS_REPORT_LABEL = "Issuer list"

LSE_ISSUERS_HEADERS = (
    "TIDM",
    "Issuer Name",
    "ISIN",
    "Market",
    "Instrument name",
    "Sector",
)

_MARKET_BY_LABEL = {
    "main market": UkMarket.MAIN,
    "main": UkMarket.MAIN,
    "aim": UkMarket.AIM,
}

_CSV_FILENAME = "issuers_report.csv"
_XLSX_FILENAME = "issuers_report.xlsx"
_DOWNLOAD_FILENAME = "issuers_report.download"
_SOURCE = CacheSource.LSE_ISSUERS
_ZIP_MAGIC = b"PK"


async def list_uk_listed_equities(
    market: str | None = None,
    symbol_prefix: str | None = None,
    name_contains: str | None = None,
    limit: int = DEFAULT_PAGE_LIMIT,
    cursor: str | None = None,
) -> ListedEquitiesPage:
    """List currently listed UK equities from the official LSE issuers report.

    Returns a paged snapshot of LSE Main Market and AIM equities. Default page
    size is 50 and the maximum is 100.

    Args:
        market: Optional market filter: ``Main`` or ``AIM``. Case is ignored.
            Omit to include both.
        symbol_prefix: Optional case-insensitive TIDM prefix (for example
            ``AZ``).
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
        market=market,
        symbol_prefix=symbol_prefix,
        name_contains=name_contains,
        limit=limit,
        cursor=cursor,
    )


async def refresh_lse_issuers() -> SourceRefreshResult:
    cache = RegulatoryDataCache.from_settings()
    with cache.publishing(_SOURCE) as (version_dir, publish):
        async with create_metadata_client() as client:
            page_response = await client.get(LSE_REPORTS_URL)
            page_response.raise_for_status()
            report_url = _discover_issuers_report_url(
                page_response.text, str(page_response.url)
            )
            download_path = version_dir / _DOWNLOAD_FILENAME
            await stream_url_to_path(client, report_url, download_path)
        report_path = _finalise_downloaded_report(download_path)
        listings, skipped_count = _parse_report(
            report_path, source_refreshed_at=utc_now()
        )
        snapshot = publish(record_count=len(listings))
    return SourceRefreshResult(
        source=_SOURCE,
        version_id=snapshot.version_id,
        downloaded_version_or_date=snapshot.downloaded_version_or_date,
        record_count=snapshot.record_count,
        cache_path=str(version_dir),
        skipped_or_idempotent_count=skipped_count,
        active_snapshot=snapshot.relative_path,
    )


def _discover_issuers_report_url(page_html: str, page_url: str) -> str:
    try:
        tree = html.fromstring(page_html)
    except (etree.ParserError, etree.XMLSyntaxError, ValueError) as exc:
        raise SchemaValidationError(
            _SOURCE, "LSE reports page could not be parsed as HTML"
        ) from exc
    expected = _normalise_report_label(LSE_ISSUERS_REPORT_LABEL)
    hrefs: list[str] = []
    for anchor in tree.xpath("//a"):
        label = _normalise_report_label("".join(anchor.itertext()))
        if label != expected and not label.endswith(expected):
            continue
        href = (anchor.get("href") or "").strip()
        if href:
            hrefs.append(href)
    unique_hrefs = list(dict.fromkeys(hrefs))
    if len(unique_hrefs) != 1:
        raise SchemaValidationError(
            _SOURCE,
            f"LSE reports page must contain exactly one '{LSE_ISSUERS_REPORT_LABEL}' "
            f"download link (found {len(unique_hrefs)}). The official HTML must include "
            "that labelled link; a JavaScript shell with no download markup cannot be used.",
        )
    return urljoin(page_url, unique_hrefs[0])


def _normalise_report_label(value: str) -> str:
    return " ".join(value.split()).casefold()


async def _load_listings(cache: RegulatoryDataCache) -> list[EquityListing]:
    snapshot, active_dir = await ensure_fresh_snapshot(
        cache, _SOURCE, refresh_lse_issuers, refresh_flags="--exchanges"
    )
    listings, _ = _parse_snapshot(active_dir, source_refreshed_at=snapshot.refreshed_at)
    return listings


def listing_for_symbol(cache: RegulatoryDataCache, symbol: str) -> EquityListing | None:
    """Return the unique cached LSE listing for ``symbol``, if a snapshot exists.

    Does not refresh. A missing or stale-unreadable snapshot yields ``None``.
    """
    snapshot = cache.snapshot_for(_SOURCE)
    active_dir = cache.active_dir(_SOURCE)
    if snapshot is None or active_dir is None:
        return None
    needle = symbol.strip().upper()
    if needle.endswith(".L"):
        needle = needle[:-2]
    if not needle:
        return None
    try:
        listings, _ = _parse_snapshot(
            active_dir, source_refreshed_at=snapshot.refreshed_at
        )
    except SchemaValidationError:
        return None
    matches = [row for row in listings if row.symbol.upper() == needle]
    if len(matches) != 1:
        return None
    return matches[0]


def _parse_snapshot(
    version_dir: Path, *, source_refreshed_at: datetime
) -> tuple[list[EquityListing], int]:
    xlsx_path = version_dir / _XLSX_FILENAME
    csv_path = version_dir / _CSV_FILENAME
    if xlsx_path.is_file():
        return _parse_report(xlsx_path, source_refreshed_at=source_refreshed_at)
    if csv_path.is_file():
        return _parse_report(csv_path, source_refreshed_at=source_refreshed_at)
    raise SchemaValidationError(_SOURCE, "issuers report is missing from the snapshot")


def _finalise_downloaded_report(download_path: Path) -> Path:
    with download_path.open("rb") as handle:
        magic = handle.read(len(_ZIP_MAGIC))
    filename = _XLSX_FILENAME if magic.startswith(_ZIP_MAGIC) else _CSV_FILENAME
    final_path = download_path.with_name(filename)
    download_path.replace(final_path)
    return final_path


def _parse_report(
    path: Path, *, source_refreshed_at: datetime
) -> tuple[list[EquityListing], int]:
    if path.suffix.casefold() == ".xlsx":
        rows = _read_xlsx_rows(path)
    else:
        rows = _read_csv_rows(path)
    return _listings_from_rows(rows, source_refreshed_at=source_refreshed_at)


def _read_csv_rows(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [list(row) for row in csv.reader(handle)]


def _read_xlsx_rows(path: Path) -> list[list[str]]:
    try:
        with zipfile.ZipFile(path) as archive:
            shared_strings = _xlsx_shared_strings(archive)
            sheet_name = _first_worksheet_name(archive)
            sheet_root = etree.fromstring(archive.read(sheet_name))
    except (OSError, KeyError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
        raise SchemaValidationError(
            _SOURCE, f"could not parse xlsx issuers report: {exc}"
        ) from exc
    return _xlsx_sheet_rows(sheet_root, shared_strings)


def _first_worksheet_name(archive: zipfile.ZipFile) -> str:
    sheet_names = sorted(
        name
        for name in archive.namelist()
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
    )
    if not sheet_names:
        raise SchemaValidationError(_SOURCE, "xlsx issuers report has no worksheet")
    return sheet_names[0]


def _xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        payload = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = etree.fromstring(payload)
    strings: list[str] = []
    for item in root.xpath(".//*[local-name()='si']"):
        text_parts = item.xpath(".//*[local-name()='t']/text()")
        strings.append("".join(text_parts))
    return strings


def _xlsx_sheet_rows(sheet_root: Any, shared_strings: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for row_element in sheet_root.xpath(
        ".//*[local-name()='sheetData']/*[local-name()='row']"
    ):
        values_by_index: dict[int, str] = {}
        next_index = 0
        for cell_element in row_element.xpath("*[local-name()='c']"):
            reference = cell_element.get("r") or ""
            try:
                index = _xlsx_column_index(reference) if reference else next_index
            except ValueError as exc:
                raise SchemaValidationError(
                    _SOURCE,
                    f"xlsx issuers report has an invalid cell reference {reference!r}",
                ) from exc
            values_by_index[index] = _xlsx_cell_text(cell_element, shared_strings)
            next_index = index + 1
        if not values_by_index:
            rows.append([])
            continue
        width = max(values_by_index) + 1
        rows.append([values_by_index.get(index, "") for index in range(width)])
    return rows


def _xlsx_column_index(cell_reference: str) -> int:
    letters = "".join(character for character in cell_reference if character.isalpha())
    if not letters:
        raise ValueError(f"invalid cell reference {cell_reference!r}")
    index = 0
    for character in letters:
        index = index * 26 + (ord(character.upper()) - ord("A") + 1)
    return index - 1


def _xlsx_cell_text(cell_element: Any, shared_strings: list[str]) -> str:
    cell_type = cell_element.get("t")
    if cell_type == "s":
        index_text = "".join(cell_element.xpath("*[local-name()='v']/text()")).strip()
        if not index_text:
            return ""
        try:
            return shared_strings[int(index_text)]
        except (IndexError, ValueError) as exc:
            raise SchemaValidationError(
                _SOURCE,
                f"xlsx issuers report has an invalid shared-string index {index_text!r}",
            ) from exc
    if cell_type == "inlineStr":
        return "".join(cell_element.xpath(".//*[local-name()='t']/text()"))
    return "".join(cell_element.xpath("*[local-name()='v']/text()"))


def _listings_from_rows(
    rows: list[list[str]], *, source_refreshed_at: datetime
) -> tuple[list[EquityListing], int]:
    if not rows:
        raise SchemaValidationError(_SOURCE, "issuers report is empty")
    header = tuple(cell.strip() for cell in rows[0])
    if header != LSE_ISSUERS_HEADERS:
        raise SchemaValidationError(
            _SOURCE,
            f"issuers report header was {list(header)!r}, expected {list(LSE_ISSUERS_HEADERS)!r}",
        )
    listings: list[EquityListing] = []
    skipped_count = 0
    for raw_row in rows[1:]:
        if not any(cell.strip() for cell in raw_row):
            continue
        padded = list(raw_row) + [""] * (len(header) - len(raw_row))
        record = dict(zip(header, padded[: len(header)], strict=True))
        listing = _listing_from_record(record, source_refreshed_at)
        if listing is None:
            skipped_count += 1
            continue
        listings.append(listing)
    return listings, skipped_count


def _listing_from_record(
    record: dict[str, str], source_refreshed_at: datetime
) -> EquityListing | None:
    instrument_name = record["Instrument name"].strip()
    if not is_ordinary_equity_instrument(instrument_name):
        return None
    if is_excluded_security_name(instrument_name):
        return None
    market = _MARKET_BY_LABEL.get(record["Market"].strip().casefold())
    if market is None:
        return None
    symbol = record["TIDM"].strip()
    issuer_name = record["Issuer Name"].strip()
    if not symbol or not issuer_name:
        return None
    isin = record["ISIN"].strip() or None
    return EquityListing(
        symbol=symbol,
        issuer_name=issuer_name,
        exchange="LSE",
        market=market,
        isin=isin,
        source=_SOURCE,
        source_refreshed_at=source_refreshed_at,
    )
