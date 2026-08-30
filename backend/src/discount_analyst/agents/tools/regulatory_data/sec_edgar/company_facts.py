import json
import re
import shutil
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from discount_analyst.agents.tools.regulatory_data import http as regulatory_http
from discount_analyst.agents.tools.regulatory_data.cache import (
    TTL_SEC_COMPANYFACTS_LIVE,
    RegulatoryDataCache,
    write_bytes_atomically,
)
from discount_analyst.agents.tools.regulatory_data.errors import (
    ColdCacheError,
    SecUserAgentMissingError,
)
from discount_analyst.agents.tools.regulatory_data.models import (
    CacheSource,
    CanonicalFundamentals,
    PeriodKind,
    SourceRefreshResult,
)
from discount_analyst.agents.tools.regulatory_data.sec_edgar.selection import (
    fundamentals_from_companyfacts,
)
from discount_analyst.agents.tools.regulatory_data.sec_edgar.submissions import (
    recent_filing_handles,
)
from discount_analyst.agents.tools.regulatory_data.sec_edgar.tickers import (
    fetch_sec_bytes,
    format_cik,
    refresh_company_tickers,
    resolve_ticker,
)

SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANYFACTS_ZIP_URL = (
    "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"
)
SEC_COMPANYFACTS_API_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEC_SUBMISSIONS_API_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

ANNUAL_FORMS = frozenset({"10-K", "10-K/A"})
QUARTERLY_FORMS = frozenset({"10-Q", "10-Q/A"})

_CIK_MEMBER_NAME = re.compile(r"^CIK\d{10}\.json$")
_STREAM_COPY_CHUNK = 64 * 1024


async def get_sec_company_facts(
    ticker: str,
    period_kind: PeriodKind = "annual",
    as_of: date | None = None,
) -> CanonicalFundamentals:
    """Return a canonical SEC companyfacts snapshot for a US ticker.

    Maps ``ticker`` to CIK via the cached SEC ticker file, then selects facts
    from one annual (10-K / 10-K/A) or quarterly (10-Q / 10-Q/A) period. The
    statement period is the latest fiscal period end among non-share facts.
    A later share-outstanding instant does not redefine that period. The
    latest filing on or before ``as_of`` wins; a later amendment for the same
    period replaces the original. Values are never mixed across period ends.

    Args:
        ticker: US listing symbol (for example ``AAPL``). Case is ignored.
        period_kind: ``annual`` (default) or ``quarterly``.
        as_of: Inclusive filing-date cutoff. Omit to use the latest available
            filing of the requested kind.

    Returns:
        One canonical fundamentals snapshot and up to five recent filing handles.
    """
    cache = RegulatoryDataCache.from_settings()
    mapped = await resolve_ticker(cache, ticker, url=SEC_COMPANY_TICKERS_URL)
    payload = await _load_companyfacts_payload(cache, mapped.cik)
    snapshot = fundamentals_from_companyfacts(
        payload,
        ticker=mapped.ticker,
        issuer_title=mapped.title,
        cik=mapped.cik,
        period_kind=period_kind,
        as_of=as_of,
        annual_forms=ANNUAL_FORMS,
        quarterly_forms=QUARTERLY_FORMS,
    )
    filings = await recent_filing_handles(
        cache,
        mapped.cik,
        url_template=SEC_SUBMISSIONS_API_URL,
        forms=ANNUAL_FORMS | QUARTERLY_FORMS,
    )
    return snapshot.model_copy(update={"recent_filings": filings})


async def refresh_sec_edgar() -> SourceRefreshResult:
    cache = RegulatoryDataCache.from_settings()
    headers = regulatory_http.sec_request_headers()
    await refresh_company_tickers(cache, SEC_COMPANY_TICKERS_URL)
    with cache.publishing(CacheSource.SEC_COMPANYFACTS) as (version_dir, publish):
        zip_path = cache.root / f".companyfacts-{version_dir.name}.zip.tmp"
        try:
            async with regulatory_http.create_bulk_client() as client:
                await regulatory_http.stream_url_to_path(
                    client,
                    SEC_COMPANYFACTS_ZIP_URL,
                    zip_path,
                    headers=headers,
                )
            record_count = _extract_companyfacts_zip(zip_path, version_dir)
            snapshot = publish(record_count=record_count)
        finally:
            zip_path.unlink(missing_ok=True)
    return SourceRefreshResult(
        source=CacheSource.SEC_COMPANYFACTS.value,
        version_id=snapshot.version_id,
        downloaded_version_or_date=snapshot.downloaded_version_or_date,
        record_count=snapshot.record_count,
        cache_path=str(cache.root / snapshot.relative_path),
        skipped_or_idempotent_count=0,
        active_snapshot=snapshot.relative_path,
    )


async def _load_companyfacts_payload(
    cache: RegulatoryDataCache,
    cik: str,
) -> object:
    padded = format_cik(cik)
    path = _existing_companyfacts_path(cache, padded)
    if path is not None:
        return json.loads(path.read_text(), parse_float=Decimal)
    return await _gap_fill_companyfacts(cache, padded)


def _existing_companyfacts_path(cache: RegulatoryDataCache, cik: str) -> Path | None:
    padded = format_cik(cik)
    filename = f"CIK{padded}.json"
    active = cache.active_dir(CacheSource.SEC_COMPANYFACTS)
    if active is not None:
        path = active / filename
        if path.is_file():
            return path
    gap_path = cache.ttl_file(TTL_SEC_COMPANYFACTS_LIVE, filename)
    if gap_path.is_file():
        return gap_path
    return None


async def _gap_fill_companyfacts(cache: RegulatoryDataCache, cik: str) -> object:
    padded = format_cik(cik)
    try:
        payload = await fetch_sec_bytes(SEC_COMPANYFACTS_API_URL.format(cik=padded))
    except SecUserAgentMissingError:
        raise
    except Exception as exc:
        raise ColdCacheError("SEC companyfacts", refresh_flags="--sec") from exc
    path = cache.ttl_file(TTL_SEC_COMPANYFACTS_LIVE, f"CIK{padded}.json")
    write_bytes_atomically(path, payload)
    return json.loads(payload, parse_float=Decimal)


def _extract_companyfacts_zip(zip_path: Path, dest_dir: Path) -> int:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_root = dest_dir.resolve()
    extracted = 0
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = Path(info.filename).name
            if not _CIK_MEMBER_NAME.match(name):
                continue
            target = (dest_dir / name).resolve()
            if not target.is_relative_to(dest_root):
                continue
            with archive.open(info) as source, target.open("wb") as handle:
                shutil.copyfileobj(source, handle, _STREAM_COPY_CHUNK)
            extracted += 1
    return extracted
