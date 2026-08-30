import csv
import zipfile
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin, urlparse

from lxml import etree

from discount_analyst.agents.tools.regulatory_data.cache import (
    RegulatoryDataCache,
    ensure_fresh_snapshot,
)
from discount_analyst.agents.tools.regulatory_data.errors import (
    ColdCacheError,
    SchemaValidationError,
)
from discount_analyst.agents.tools.regulatory_data.exchanges.equity_classifier import (
    is_excluded_security_name,
)
from discount_analyst.agents.tools.regulatory_data.http import (
    create_metadata_client,
    stream_url_to_path,
)
from discount_analyst.agents.tools.regulatory_data.json_maps import (
    as_object_list,
    as_str_map,
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

LSE_PAGES_URL = "https://api.londonstockexchange.com/api/v1/pages?path=reports"
LSE_COMPONENTS_REFRESH_URL = (
    "https://api.londonstockexchange.com/api/v1/components/refresh"
)
LSE_REPORTS_PATH = "reports"
LSE_PARENT_FILTER_LABEL = "Issuers and Instruments"
LSE_INSTRUMENTS_SUBFILTER_LABEL = "Instruments"
LSE_INSTRUMENT_LIST_CTA_TITLE = "Instrument list"
LSE_SHARES_SHEET_NAME = "1.1 Shares"

LSE_INSTRUMENT_COLUMNS = (
    "TIDM",
    "Issuer Name",
    "Instrument Name",
    "ISIN",
    "LSE Market",
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
_WORKBOOK_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


@dataclass(frozen=True, slots=True)
class _InstrumentsTab:
    tab: str
    tab_id: str
    module_id: str


async def list_uk_listed_equities(
    market: str | None = None,
    symbol_prefix: str | None = None,
    name_contains: str | None = None,
    limit: int = DEFAULT_PAGE_LIMIT,
    cursor: str | None = None,
) -> ListedEquitiesPage:
    """List currently listed UK equities from the official LSE instrument list.

    Returns a paged snapshot of LSE Main Market and AIM shares. Default page
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
            pages_response = await client.get(LSE_PAGES_URL)
            pages_response.raise_for_status()
            refresh_response = await client.post(
                LSE_COMPONENTS_REFRESH_URL,
                json=_refresh_body(_instruments_tab(pages_response.json())),
            )
            refresh_response.raise_for_status()
            report_url = _instrument_list_url(refresh_response.json())
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


def _sole[T](items: Iterable[T], *, what: str) -> T:
    found = list(items)
    if len(found) != 1:
        raise SchemaValidationError(
            _SOURCE,
            f"LSE instrument list must contain exactly one {what} (found {len(found)})",
        )
    return found[0]


def _normalise_report_label(value: str) -> str:
    return " ".join(value.split()).casefold()


def _json_objects(node: object) -> Iterator[dict[str, object]]:
    mapping = as_str_map(node)
    if mapping is not None:
        yield mapping
        for value in mapping.values():
            yield from _json_objects(value)
        return
    items = as_object_list(node)
    if items is not None:
        for item in items:
            yield from _json_objects(item)


def _label_is(node: dict[str, object], expected: str, *, key: str) -> bool:
    value = node.get(key)
    return isinstance(value, str) and _normalise_report_label(
        value
    ) == _normalise_report_label(expected)


def _required_text(node: dict[str, object], key: str, *, what: str) -> str:
    value = node.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SchemaValidationError(_SOURCE, f"{what} is missing {key!r}")
    return value.strip()


def _instruments_tab(pages_json: object) -> _InstrumentsTab:
    parent = _sole(
        (
            node
            for node in _json_objects(pages_json)
            if _label_is(node, LSE_PARENT_FILTER_LABEL, key="label")
        ),
        what=f"parent filter labelled {LSE_PARENT_FILTER_LABEL!r}",
    )
    subfilter = _sole(
        (
            node
            for item in (as_object_list(parent.get("subFilters")) or [])
            if (node := as_str_map(item)) is not None
            and _label_is(node, LSE_INSTRUMENTS_SUBFILTER_LABEL, key="label")
        ),
        what=f"subfilter labelled {LSE_INSTRUMENTS_SUBFILTER_LABEL!r}",
    )
    module_payload = _sole(
        as_object_list(subfilter.get("modules")) or [],
        what="module on the Instruments subfilter",
    )
    module = as_str_map(module_payload)
    if module is None:
        raise SchemaValidationError(_SOURCE, "Instruments module is not an object")
    return _InstrumentsTab(
        tab=_normalise_report_label(
            _required_text(subfilter, "label", what="Instruments subfilter")
        ),
        tab_id=_required_text(subfilter, "tabId", what="Instruments subfilter"),
        module_id=_required_text(module, "moduleId", what="Instruments module"),
    )


def _refresh_body(tab: _InstrumentsTab) -> dict[str, object]:
    return {
        "path": LSE_REPORTS_PATH,
        "parameters": urlencode({"tab": tab.tab, "tabId": tab.tab_id}),
        "components": [{"componentId": tab.module_id, "parameters": None}],
    }


def _instrument_list_url(refresh_json: object) -> str:
    cta = _sole(
        (
            node
            for node in _json_objects(refresh_json)
            if _label_is(node, LSE_INSTRUMENT_LIST_CTA_TITLE, key="ctaTitle")
        ),
        what=f"ctaTitle {LSE_INSTRUMENT_LIST_CTA_TITLE!r}",
    )
    button = as_str_map(cta.get("ctaButton"))
    if button is None:
        raise SchemaValidationError(
            _SOURCE, "Instrument list ctaItem is missing ctaButton"
        )
    href = _required_text(button, "link", what="Instrument list ctaButton")
    absolute = urljoin("https://www.londonstockexchange.com/", href)
    if urlparse(absolute).scheme not in {"http", "https"}:
        raise SchemaValidationError(
            _SOURCE, "Instrument list link is not an http(s) URL"
        )
    return absolute


async def _load_listings(cache: RegulatoryDataCache) -> list[EquityListing]:
    snapshot, active_dir = await ensure_fresh_snapshot(
        cache, _SOURCE, refresh_lse_issuers, refresh_flags="--exchanges"
    )
    try:
        listings, _ = _parse_snapshot(
            active_dir, source_refreshed_at=snapshot.refreshed_at
        )
    except SchemaValidationError as exc:
        await refresh_lse_issuers()
        snapshot = cache.snapshot_for(_SOURCE)
        active_dir = cache.active_dir(_SOURCE)
        if snapshot is None or active_dir is None:
            raise ColdCacheError(str(_SOURCE), refresh_flags="--exchanges") from exc
        listings, _ = _parse_snapshot(
            active_dir, source_refreshed_at=snapshot.refreshed_at
        )
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
            sheet_name = _shares_worksheet_path(archive)
            sheet_root = etree.fromstring(archive.read(sheet_name))
    except (OSError, KeyError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
        raise SchemaValidationError(
            _SOURCE, f"could not parse xlsx issuers report: {exc}"
        ) from exc
    return _xlsx_sheet_rows(sheet_root, shared_strings)


def _shares_worksheet_path(archive: zipfile.ZipFile) -> str:
    try:
        workbook = etree.fromstring(archive.read("xl/workbook.xml"))
        rels_root = etree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    except KeyError as exc:
        raise SchemaValidationError(
            _SOURCE, "xlsx instrument list is missing workbook metadata"
        ) from exc
    targets = {
        rel.get("Id"): rel.get("Target")
        for rel in rels_root
        if rel.get("Id") and rel.get("Target")
    }
    expected = _normalise_report_label(LSE_SHARES_SHEET_NAME)
    matches: list[str] = []
    for sheet in workbook.xpath(".//*[local-name()='sheet']"):
        name = sheet.get("name") or ""
        if _normalise_report_label(name) != expected:
            continue
        relationship_id = sheet.get(f"{{{_WORKBOOK_REL_NS}}}id")
        target = targets.get(relationship_id or "")
        if target:
            matches.append(_xlsx_rel_target_to_member(target))
    return _sole(matches, what=f"worksheet named {LSE_SHARES_SHEET_NAME!r}")


def _xlsx_rel_target_to_member(target: str) -> str:
    cleaned = target.lstrip("/")
    if cleaned.startswith("xl/"):
        return cleaned
    return f"xl/{cleaned}"


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
    header_index = _header_row_index(rows)
    header = tuple(cell.strip() for cell in rows[header_index])
    column_indexes = _column_indexes(header)
    listings: list[EquityListing] = []
    skipped_count = 0
    for raw_row in rows[header_index + 1 :]:
        if not any(cell.strip() for cell in raw_row):
            continue
        padded = list(raw_row) + [""] * (len(header) - len(raw_row))
        record = {
            column: padded[column_indexes[column]] for column in LSE_INSTRUMENT_COLUMNS
        }
        listing = _listing_from_record(record, source_refreshed_at)
        if listing is None:
            skipped_count += 1
            continue
        listings.append(listing)
    return listings, skipped_count


def _header_row_index(rows: list[list[str]]) -> int:
    required = {_normalise_report_label(name) for name in LSE_INSTRUMENT_COLUMNS}
    matches = [
        index
        for index, row in enumerate(rows)
        if required <= {_normalise_report_label(cell) for cell in row if cell.strip()}
    ]
    return _sole(matches, what="instrument-list header row")


def _column_indexes(header: tuple[str, ...]) -> dict[str, int]:
    found: dict[str, list[int]] = {column: [] for column in LSE_INSTRUMENT_COLUMNS}
    expected = {
        _normalise_report_label(column): column for column in LSE_INSTRUMENT_COLUMNS
    }
    for index, name in enumerate(header):
        column = expected.get(_normalise_report_label(name))
        if column is None:
            continue
        found[column].append(index)
    return {
        column: _sole(indexes, what=f"header column {column!r}")
        for column, indexes in found.items()
    }


def _listing_from_record(
    record: dict[str, str], source_refreshed_at: datetime
) -> EquityListing | None:
    instrument_name = record["Instrument Name"].strip()
    if is_excluded_security_name(instrument_name):
        return None
    market = _MARKET_BY_LABEL.get(record["LSE Market"].strip().casefold())
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
