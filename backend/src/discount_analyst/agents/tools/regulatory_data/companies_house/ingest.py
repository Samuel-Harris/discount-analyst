import calendar
import csv
import io
import re
import shutil
import sqlite3
import tempfile
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

from lxml import etree

from discount_analyst.agents.tools.regulatory_data.companies_house.concepts import (
    map_facts,
)
from discount_analyst.agents.tools.regulatory_data.companies_house.ixbrl import (
    parse_ixbrl,
)
from discount_analyst.agents.tools.regulatory_data.companies_house.store import (
    fetch_company_by_number,
    insert_account,
    upsert_company,
)
from discount_analyst.agents.tools.regulatory_data.errors import SchemaValidationError

COMPANIES_INDEX_URL = "http://download.companieshouse.gov.uk/en_output.html"
DAILY_ACCOUNTS_INDEX_URL = "https://download.companieshouse.gov.uk/en_accountsdata.html"
MONTHLY_ACCOUNTS_INDEX_URL = (
    "https://download.companieshouse.gov.uk/en_monthlyaccountsdata.html"
)
TRAILING_MONTHLY_ARCHIVES = 18

COMPANY_CSV_HEADERS = (
    "CompanyName",
    "CompanyNumber",
    "RegAddress.AddressLine1",
    "CompanyStatus",
    "CompanyCategory",
    "DissolutionDate",
    "IncorporationDate",
)

_COMPANY_ONE_FILE = re.compile(
    r"BasicCompanyDataAsOneFile-(\d{4}-\d{2}-\d{2})\.zip$", re.IGNORECASE
)
_COMPANY_PART_FILE = re.compile(
    r"BasicCompanyData-\d{4}-\d{2}-\d{2}-part\d+_\d+\.zip$", re.IGNORECASE
)
_MONTHLY_ARCHIVE = re.compile(
    r"Accounts_Monthly_Data-([A-Za-z]+)(\d{4})\.zip$", re.IGNORECASE
)
_DAILY_ARCHIVE = re.compile(
    r"Accounts_Bulk_Data-(\d{4}-\d{2}-\d{2})\.zip$", re.IGNORECASE
)
_ACCOUNT_MEMBER = re.compile(
    r"(?P<company>[A-Z0-9]{8})_(?P<period>\d{8})\."
    r"(?P<ext>html|xhtml|htm|xml|zip)$",
    re.IGNORECASE,
)
_MONTH_NUMBER: dict[str, int] = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


@dataclass(frozen=True, slots=True)
class IngestResult:
    inserted_count: int
    skipped_or_idempotent_count: int


def normalise_text(value: str) -> str:
    collapsed = " ".join(value.split())
    folded = collapsed.casefold()
    if folded.endswith(".l"):
        folded = folded[:-2].rstrip()
    return folded


def canonical_company_number(value: str) -> str | None:
    compact = value.strip().upper().replace(" ", "")
    if not compact:
        return None
    if compact.isdigit() and len(compact) <= 8:
        return compact.zfill(8)
    if re.fullmatch(r"[A-Z0-9]{8}", compact) and any(ch.isdigit() for ch in compact):
        return compact
    return None


def ingest_companies_csv(connection: sqlite3.Connection, path: Path) -> int:
    text = _read_csv_text(path)
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []
    missing = [header for header in COMPANY_CSV_HEADERS if header not in fieldnames]
    if missing:
        raise SchemaValidationError(
            "Companies House",
            f"company CSV missing headers {missing}; present={list(fieldnames)}",
        )
    inserted = 0
    for row in reader:
        company_number = canonical_company_number(row.get("CompanyNumber") or "")
        company_name = (row.get("CompanyName") or "").strip()
        if company_number is None or not company_name:
            continue
        upsert_company(
            connection,
            company_number=company_number,
            company_name=company_name,
            company_status=_optional(row.get("CompanyStatus")),
            company_type=_optional(row.get("CompanyCategory")),
            name_normalised=normalise_text(company_name),
        )
        inserted += 1
    connection.commit()
    return inserted


def ingest_account_ixbrl(
    connection: sqlite3.Connection,
    company_number: str,
    filed_at: date,
    period_end: date,
    xhtml_path: Path,
    source_document_id: str,
) -> IngestResult:
    parsed = parse_ixbrl(xhtml_path)
    mapped = map_facts(parsed.facts)
    number = canonical_company_number(company_number) or company_number.strip()
    issuer_name = parsed.issuer_name
    if issuer_name is None:
        company = fetch_company_by_number(connection, number)
        if company is not None:
            issuer_name = company["company_name"]
    inserted = insert_account(
        connection,
        source_document_id=source_document_id,
        company_number=number,
        filed_at=filed_at,
        period_end=period_end,
        currency=parsed.currency,
        issuer_name=issuer_name,
        revenue=mapped.revenue,
        net_income=mapped.net_income,
        total_assets=mapped.total_assets,
        total_liabilities=mapped.total_liabilities,
        equity=mapped.equity,
        cash=mapped.cash,
        debt=mapped.debt,
        shares_outstanding=mapped.shares_outstanding,
        accounts_filleted=mapped.accounts_filleted,
        profit_and_loss_available=mapped.profit_and_loss_available,
    )
    connection.commit()
    if inserted:
        return IngestResult(inserted_count=1, skipped_or_idempotent_count=0)
    return IngestResult(inserted_count=0, skipped_or_idempotent_count=1)


def ingest_companies_zip(connection: sqlite3.Connection, zip_path: Path) -> int:
    total = 0
    with zipfile.ZipFile(zip_path) as archive:
        csv_names = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".csv") and not name.endswith("/")
        ]
        if not csv_names:
            raise SchemaValidationError(
                "Companies House", "company archive contains no CSV"
            )
        for name in csv_names:
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            try:
                with archive.open(name) as source, tmp_path.open("wb") as dest:
                    shutil.copyfileobj(source, dest)
                total += ingest_companies_csv(connection, tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)
    return total


def ingest_accounts_zip(
    connection: sqlite3.Connection,
    zip_path: Path,
    *,
    filed_at: date,
    source_prefix: str,
    nested_depth: int = 0,
) -> IngestResult:
    if nested_depth > 2:
        return IngestResult(inserted_count=0, skipped_or_idempotent_count=0)
    inserted = 0
    skipped = 0
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            member_name = info.filename
            basename = Path(member_name).name
            match = _ACCOUNT_MEMBER.search(basename)
            if match is None:
                skipped += 1
                continue
            extension = match.group("ext").lower()
            company_number = match.group("company").upper()
            period_end = date.fromisoformat(_iso_from_yyyymmdd(match.group("period")))
            source_document_id = f"{source_prefix}/{member_name}"
            with tempfile.NamedTemporaryFile(
                suffix=f".{extension}", delete=False
            ) as tmp:
                tmp_path = Path(tmp.name)
            try:
                with archive.open(info) as source, tmp_path.open("wb") as dest:
                    shutil.copyfileobj(source, dest)
                if extension == "zip":
                    nested = ingest_accounts_zip(
                        connection,
                        tmp_path,
                        filed_at=filed_at,
                        source_prefix=source_document_id,
                        nested_depth=nested_depth + 1,
                    )
                    inserted += nested.inserted_count
                    skipped += nested.skipped_or_idempotent_count
                    continue
                if extension == "xml":
                    skipped += 1
                    continue
                result = ingest_account_ixbrl(
                    connection,
                    company_number,
                    filed_at,
                    period_end,
                    tmp_path,
                    source_document_id,
                )
                inserted += result.inserted_count
                skipped += result.skipped_or_idempotent_count
            finally:
                tmp_path.unlink(missing_ok=True)
    return IngestResult(inserted_count=inserted, skipped_or_idempotent_count=skipped)


def zip_hrefs_from_html(html: str) -> list[str]:
    tree = etree.HTML(html)
    hrefs: list[str] = []
    for element in tree.xpath("//a[@href]"):
        href = element.get("href")
        if href and href.lower().endswith(".zip"):
            hrefs.append(str(href).strip())
    return hrefs


def select_company_data_href(hrefs: Iterable[str]) -> str | None:
    one_file: list[tuple[date, str]] = []
    parts: list[str] = []
    for href in hrefs:
        filename = Path(href.split("?", 1)[0]).name
        match = _COMPANY_ONE_FILE.search(filename)
        if match:
            one_file.append((date.fromisoformat(match.group(1)), href))
            continue
        if _COMPANY_PART_FILE.search(filename):
            parts.append(href)
    if one_file:
        one_file.sort(key=lambda item: item[0], reverse=True)
        return one_file[0][1]
    return parts[0] if parts else None


def select_monthly_archive_hrefs(
    hrefs: Iterable[str], *, limit: int = TRAILING_MONTHLY_ARCHIVES
) -> list[tuple[date, str]]:
    parsed: list[tuple[date, str]] = []
    for href in hrefs:
        filename = Path(href.split("?", 1)[0]).name
        match = _MONTHLY_ARCHIVE.search(filename)
        if match is None:
            continue
        month = _MONTH_NUMBER.get(match.group(1).casefold())
        if month is None:
            continue
        year = int(match.group(2))
        last_day = calendar.monthrange(year, month)[1]
        parsed.append((date(year, month, last_day), href))
    parsed.sort(key=lambda item: item[0], reverse=True)
    return list(reversed(parsed[:limit]))


def select_daily_archive_hrefs(
    hrefs: Iterable[str], *, after: date | None
) -> list[tuple[date, str]]:
    parsed: list[tuple[date, str]] = []
    for href in hrefs:
        filename = Path(href.split("?", 1)[0]).name
        match = _DAILY_ARCHIVE.search(filename)
        if match is None:
            continue
        archive_date = date.fromisoformat(match.group(1))
        if after is not None and archive_date <= after:
            continue
        parsed.append((archive_date, href))
    parsed.sort(key=lambda item: item[0])
    return parsed


def absolute_download_url(index_url: str, href: str) -> str:
    return urljoin(index_url, href)


def _read_csv_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _iso_from_yyyymmdd(value: str) -> str:
    return f"{value[0:4]}-{value[4:6]}-{value[6:8]}"
