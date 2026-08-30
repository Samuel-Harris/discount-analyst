import json
from datetime import date
from pathlib import Path

from discount_analyst.agents.tools.regulatory_data.cache import (
    TTL_SEC_SUBMISSIONS,
    RegulatoryDataCache,
    write_bytes_atomically,
)
from discount_analyst.agents.tools.regulatory_data.json_maps import (
    as_object_list,
    as_str_map,
)
from discount_analyst.agents.tools.regulatory_data.models import FilingHandle
from discount_analyst.agents.tools.regulatory_data.sec_edgar.tickers import (
    fetch_sec_bytes,
    format_cik,
)

_MAX_RECENT_FILINGS = 5
_ARCHIVES_URL = (
    "https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_nodashes}/{primary}"
)


def submissions_cache_path(cache: RegulatoryDataCache, cik: str) -> Path:
    return cache.ttl_file(TTL_SEC_SUBMISSIONS, f"CIK{format_cik(cik)}.json")


async def recent_filing_handles(
    cache: RegulatoryDataCache,
    cik: str,
    *,
    url_template: str,
    forms: frozenset[str],
) -> list[FilingHandle]:
    padded = format_cik(cik)
    path = submissions_cache_path(cache, padded)
    if not cache.file_is_fresh(path):
        try:
            payload = await fetch_sec_bytes(url_template.format(cik=padded))
            write_bytes_atomically(path, payload)
        except Exception:
            if not path.is_file():
                return []
    if not path.is_file():
        return []
    try:
        return parse_recent_filings(path.read_bytes(), cik=padded, forms=forms)
    except (json.JSONDecodeError, TypeError, ValueError, KeyError):
        return []


def parse_recent_filings(
    raw: bytes,
    *,
    cik: str,
    forms: frozenset[str],
) -> list[FilingHandle]:
    payload_map = as_str_map(json.loads(raw))
    if payload_map is None:
        return []
    filings_map = as_str_map(payload_map.get("filings"))
    if filings_map is None:
        return []
    recent_map = as_str_map(filings_map.get("recent"))
    if recent_map is None:
        return []
    accessions = _string_list(recent_map.get("accessionNumber"))
    form_types = _string_list(recent_map.get("form"))
    filing_dates = _string_list(recent_map.get("filingDate"))
    report_dates = _string_list(recent_map.get("reportDate"))
    primaries = _string_list(recent_map.get("primaryDocument"))
    count = min(
        len(accessions),
        len(form_types),
        len(filing_dates),
        len(report_dates),
        len(primaries),
    )
    cik_int = int(format_cik(cik))
    handles: list[FilingHandle] = []
    for index in range(count):
        form_type = form_types[index]
        if form_type not in forms:
            continue
        report_date = report_dates[index]
        filing_date = filing_dates[index]
        accession = accessions[index]
        primary = primaries[index]
        if not report_date or not filing_date or not accession or not primary:
            continue
        try:
            handles.append(
                FilingHandle(
                    form_type=form_type,
                    period_end=date.fromisoformat(report_date),
                    filed_at=date.fromisoformat(filing_date),
                    accession_or_document_id=accession,
                    source_url=_ARCHIVES_URL.format(
                        cik_int=cik_int,
                        accession_nodashes=accession.replace("-", ""),
                        primary=primary,
                    ),
                )
            )
        except ValueError:
            continue
    handles.sort(key=lambda handle: (handle.filed_at, handle.period_end), reverse=True)
    return handles[:_MAX_RECENT_FILINGS]


def _string_list(value: object) -> list[str]:
    items = as_object_list(value)
    if items is None:
        return []
    return [str(item) for item in items]
