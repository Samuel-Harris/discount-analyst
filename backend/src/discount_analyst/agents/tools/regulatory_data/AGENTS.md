<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-08-30 | Updated: 2026-08-30 -->

# regulatory_data

## Purpose

£0 official-source tools for US/UK listed-equity universes and filing-derived fundamentals. NASDAQ Trader and the LSE issuers report confirm symbols; SEC companyfacts and Companies House iXBRL supply compact snapshots. Surveyor screens with yfinance and uses these tools for official listing and filing verification; FMP/EODHD is not the primary screening path.

## Key Files

| File            | Description                                                                 |
| --------------- | --------------------------------------------------------------------------- |
| `models.py`     | `EquityListing`, `ListedEquitiesPage`, `CanonicalFundamentals`, refresh DTOs |
| `cache.py`      | Versioned bulk snapshots; file-TTL overlays for SEC tickers/submissions/gap-fill |
| `http.py`       | 30s metadata client, streamed bulk downloads, SEC User-Agent headers        |
| `pagination.py` | Shared listing filters; default page 50, cap 100                            |
| `errors.py`     | `ColdCacheError` names `discount-analyst admin refresh-regulatory-data`     |
| `toolsets.py`   | `create_universe_toolset()` and `create_filings_toolset()`                  |
| `refresh.py`    | Flag resolution and per-source refresh orchestration                        |
| `json_maps.py`  | Typed JSON object/list casts for SEC payloads                               |

## Subdirectories

| Directory           | Purpose                                              |
| ------------------- | ---------------------------------------------------- |
| `exchanges/`        | NASDAQ Trader merge/filter and LSE issuers report    |
| `sec_edgar/`        | Ticker→CIK, companyfacts selection, submissions TTL  |
| `companies_house/`  | Company product ingest, iXBRL parse, SQLite store    |

## For AI Agents

### Working In This Directory

- Preserve reported values as `Decimal`; never coerce binary floats into fundamentals.
- Publish a new cache version only after validation. Failure must leave the previous manifest active.
- The live LSE reports page is a JavaScript shell with no download markup. `refresh_lse_issuers` fails with `SchemaValidationError` until the official HTML includes a labelled Issuer list link. Do not substitute the FCA Official List or paid LSEG feeds.
- SEC requests need `SEC__USER_AGENT`. A missing value blocks SEC refresh/gap-fill, not listings or Companies House.
- Stale SEC ticker and submissions files are served when a live refresh fails.
- Companies House iXBRL facts are taken from the latest context period, not document order.
- Do not download multi-gigabyte archives inside an agent tool call. Bulk refresh is `discount-analyst admin refresh-regulatory-data`.
- Ambiguous UK identity is data (`selected=None`), not a guessed match.

### Testing Requirements

- Mock HTTP. Fixtures: `backend/tests/fixtures/regulatory_data/`.
- Tests: `backend/tests/discount_analyst/integrations/test_*nasdaq*`, `test_*london*`, `test_sec_edgar.py`, `test_companies_house.py`, `test_regulatory_data_*.py`, `test_refresh_regulatory_data.py`.

## Dependencies

### Internal

- `discount_analyst.config.settings`, `discount_analyst.agents.tools.http.retrying_client`.

### External

- **httpx**, **lxml**, **pydantic**.
