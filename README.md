# Discount Analyst

[![CI](https://github.com/Samuel-Harris/discount-analyst/actions/workflows/ci.yml/badge.svg)](https://github.com/Samuel-Harris/discount-analyst/actions/workflows/ci.yml)

An AI-powered stock analysis tool for identifying and valuing promising small-cap UK and US equities. The name "Discount Analyst" reflects two goals: it is designed to find stocks trading at a discount to intrinsic value, and to do so cheaply — minimising manual effort and API costs.

## Investment Workflow

The tool supports a six-stage pipeline that blends automated AI agents with a lightweight manual review step:

**1. Survey — discover candidates**
Run the Surveyor agent to screen for promising small-cap stocks across UK and US markets:

```bash
uv run python scripts/run_surveyor.py
```

The agent uses AI-powered web research to surface a ranked list of candidates with market caps, exchange listings, and a rationale for each.

**2. Shortlist — human review**
Manually review the Surveyor output and select the top ~10 most promising candidates.

**3. Categorise — value or growth**
For each shortlisted stock, decide whether it is a **value** stock (trading below intrinsic value, mature business) or a **growth** stock (high-growth, often pre-profit).

**4. Deep research — qualitative analysis**
Use an AI model (ChatGPT or Gemini) with a structured deep-research prompt to produce a comprehensive research report for each stock. The prompts differ by category:

- Value stocks: assessed on financial health, valuation multiples, competitive moats, balance sheet strength, and red flags.
- Growth stocks: assessed on revenue growth quality, unit economics, market opportunity, product differentiation, customer metrics, and catalysts.

An AI agent then scores the resulting report against a detailed checklist for the appropriate category and produces a pass/fail summary per section.

**5. Value — DCF analysis**
Stocks that pass enough checklist criteria are passed to the Appraiser agent for a full Discounted Cash Flow valuation:

```bash
uv run python scripts/run_dcf_analysis.py --ticker <TICKER> --risk-free-rate <RATE> --research-report-path <path/to/report.md>
```

**6. Buy — act on the margin of safety**
Review the DCF outputs across all analysed stocks. Buy the stocks with the greatest margin of safety — i.e. where the current market price is furthest below the intrinsic value estimated by the Appraiser.

## Quick Start

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) if needed
2. Set up your environment variables (see [scripts/README.md](scripts/README.md))
3. Install dependencies: `uv sync`
4. Run the Surveyor to find candidates: `uv run python scripts/run_surveyor.py`
5. After shortlisting and research (steps 2–4 above), run DCF analysis: `uv run python scripts/run_dcf_analysis.py --ticker <ticker> --risk-free-rate <risk free rate> --research-report-path <path to your research report (markdown format only)>`
