import json
from dataclasses import dataclass
from pathlib import Path

from discount_analyst.agents.tools.regulatory_data import http as regulatory_http
from discount_analyst.agents.tools.regulatory_data.cache import (
    TTL_SEC_TICKERS,
    RegulatoryDataCache,
    write_bytes_atomically,
)
from discount_analyst.agents.tools.regulatory_data.errors import (
    ColdCacheError,
    UnknownTickerError,
)
from discount_analyst.agents.tools.regulatory_data.json_maps import as_str_map

_TICKERS_FILENAME = "company_tickers.json"


@dataclass(frozen=True, slots=True)
class SecTicker:
    ticker: str
    cik: str
    title: str


def format_cik(cik: object) -> str:
    return str(cik).strip().zfill(10)


def tickers_cache_path(cache: RegulatoryDataCache) -> Path:
    return cache.ttl_file(TTL_SEC_TICKERS, _TICKERS_FILENAME)


def normalise_ticker(ticker: str) -> str:
    return ticker.strip().upper()


async def fetch_sec_bytes(url: str) -> bytes:
    headers = regulatory_http.sec_request_headers()
    async with regulatory_http.create_metadata_client() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.content


async def refresh_company_tickers(cache: RegulatoryDataCache, url: str) -> Path:
    payload = await fetch_sec_bytes(url)
    path = tickers_cache_path(cache)
    write_bytes_atomically(path, payload)
    return path


async def resolve_ticker(
    cache: RegulatoryDataCache,
    ticker: str,
    *,
    url: str,
) -> SecTicker:
    symbol = normalise_ticker(ticker)
    mapping = await load_ticker_mapping(cache, url=url)
    matched = mapping.get(symbol)
    if matched is None:
        raise UnknownTickerError(symbol)
    return matched


async def load_ticker_mapping(
    cache: RegulatoryDataCache,
    *,
    url: str,
) -> dict[str, SecTicker]:
    path = tickers_cache_path(cache)
    if not cache.file_is_fresh(path):
        try:
            await refresh_company_tickers(cache, url)
        except Exception as exc:
            if not path.is_file():
                raise ColdCacheError(
                    "SEC company tickers", refresh_flags="--sec"
                ) from exc
    if not path.is_file():
        raise ColdCacheError("SEC company tickers", refresh_flags="--sec")
    return parse_company_tickers(path.read_bytes())


def parse_company_tickers(raw: bytes) -> dict[str, SecTicker]:
    payload_map = as_str_map(json.loads(raw))
    if payload_map is None:
        raise ValueError("SEC company_tickers.json must be an object")
    mapping: dict[str, SecTicker] = {}
    for entry in payload_map.values():
        entry_map = as_str_map(entry)
        if entry_map is None:
            continue
        ticker = normalise_ticker(str(entry_map.get("ticker") or ""))
        cik_raw = entry_map.get("cik_str")
        if not ticker or cik_raw is None or cik_raw == "":
            continue
        mapping[ticker] = SecTicker(
            ticker=ticker,
            cik=format_cik(cik_raw),
            title=str(entry_map.get("title") or ticker),
        )
    return mapping
