<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-08-30 | Updated: 2026-09-30 -->

# tools

## Purpose

Agent-facing tool clients used by pipeline factories: web research, FX conversion, financial MCP, the docker-backed terminal, and official regulatory-data listings/filings.

## Key Files

| File           | Description                                                                 |
| -------------- | --------------------------------------------------------------------------- |
| `screening.py` | Surveyor-only `compute_screening_metrics` host tool. Calls `domain/screening/metrics.py`. |

## Subdirectories

| Directory          | Purpose                                                                 |
| ------------------ | ----------------------------------------------------------------------- |
| `market_data/`     | Frankfurter FX and FMP/EODHD MCP toolsets                               |
| `web_research/`    | Perplexity, bounded DuckDuckGo search, text-only web fetch              |
| `terminal/`        | Terminal HTTP client and `InfallibleToolset`                            |
| `regulatory_data/` | Official NASDAQ/LSE listings and SEC/Companies House filings (see `regulatory_data/AGENTS.md`) |

## For AI Agents

### Working In This Directory

- Register new agent tools as `InfallibleToolset` wrapping a `FunctionToolset`, following `market_data/frankfurter.py`.
- Do not add paid-API substitutes for official regulatory sources. Cache bulk artefacts under gitignored `data/regulatory_data/`.

### Testing Requirements

- Integration tests live under `backend/tests/discount_analyst/integrations/`.

## Dependencies

### Internal

- `discount_analyst.config.settings`, `discount_analyst.config.rate_limit_client`, `discount_analyst.agents.runtime`.

### External

- **httpx**, **pydantic-ai**, **lxml** (regulatory iXBRL / LSE xlsx).
