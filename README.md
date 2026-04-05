# Discount Analyst

[![CI](https://github.com/Samuel-Harris/discount-analyst/actions/workflows/ci.yml/badge.svg)](https://github.com/Samuel-Harris/discount-analyst/actions/workflows/ci.yml)

An AI-powered stock analysis tool for identifying and valuing promising small-cap UK and US equities. The name "Discount Analyst" reflects two goals: it is designed to find stocks trading at a discount to intrinsic value, and to do so cheaply — minimising manual effort and API costs.

## Investment Workflow

The tool supports a five-stage pipeline: Surveyor, Researcher, and Strategist run in-repo; you still use an external AI model to weigh the buy case after DCF, then decide trades yourself.

**1. Survey — discover candidates**
Run the Surveyor agent to screen for promising small-cap stocks across UK and US markets:

```bash
uv run python scripts/agents/run_surveyor.py
```

The agent uses AI-powered web research to surface a ranked list of candidates with market caps, exchange listings, and a rationale for each.

**2. Research & strategy — in-repo agents**
The **Researcher** agent takes each `SurveyorCandidate` (value vs growth is part of the surveyor context) and produces a structured, neutral **deep research** report (`DeepResearchReport`). The **Strategist** agent then reads that report plus the same candidate and outputs a structured **mispricing thesis** (`MispricingThesis`) — interpretation only, no extra web research.

Run the full chain (Surveyor → Researcher → Strategist) in one go:

```bash
uv run python scripts/workflows/run_surveyor_researcher_strategist.py
```

Or run agents separately after Surveyor, using selectors of the form `path/to/surveyor.json` (all candidates) or `path/to/surveyor.json:TICKER` (one ticker):

```bash
uv run python scripts/agents/run_researcher.py --surveyor-report-and-ticker <selector>
uv run python scripts/agents/run_strategist.py --researcher-report-and-ticker <selector>
```

You can still narrow scope by passing a single-ticker selector instead of treating “shortlist” and “categorise” as separate manual stages.

**3. Value — DCF analysis**
Pass names that are ready for valuation to the Appraiser agent for a full Discounted Cash Flow analysis:

```bash
uv run python scripts/agents/run_appraiser.py \
  --sentinel-report-and-ticker scripts/outputs/<sentinel-run>.json \
  --risk-free-rate <RATE>
```

Use the Sentinel artifact written under `scripts/outputs/` after `run_sentinel.py` (or the full pipeline). The script follows the same `path.json` / `path.json:TICKER` selector pattern as Sentinel; it loads Surveyor, Researcher, and Strategist JSON paths from fields inside the Sentinel run record.

**4. Evaluate — AI buy recommendation**
Use an AI model (Claude, Gemini, or ChatGPT) to evaluate whether to buy each stock based on the research report, Strategist thesis, and the DCF analysis output.

**5. Buy — act on the margin of safety**
Review the DCF outputs across all analysed stocks. Buy the stocks with the greatest margin of safety — i.e. where the current market price is furthest below the intrinsic value estimated by the Appraiser.

## Quick Start

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) if needed
2. Set up your environment variables (see [scripts/README.md](scripts/README.md))
3. Install dependencies: `uv sync`
4. Run the Surveyor to find candidates: `uv run python scripts/agents/run_surveyor.py`, or run survey → research → strategy in one command: `uv run python scripts/workflows/run_surveyor_researcher_strategist.py`
5. After Researcher/Strategist/Sentinel (step 2 above — or `scripts/workflows/run_surveyor_to_appraiser.py` for the full gated pipeline), run DCF analysis: `uv run python scripts/agents/run_appraiser.py --sentinel-report-and-ticker scripts/outputs/<sentinel>.json --risk-free-rate <decimal e.g. 0.045>`
