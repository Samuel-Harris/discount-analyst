# Discount Analyst

[![CI](https://github.com/Samuel-Harris/discount-analyst/actions/workflows/ci.yml/badge.svg)](https://github.com/Samuel-Harris/discount-analyst/actions/workflows/ci.yml)

An AI-powered stock analysis tool. It was named 'Discount Analyst' because it is intended to be a cheap stock analysis tool.

It is intended to be cheap to run and automated, requiring little manual input.

## Quick Start

To perform a Discounted Cash Flow (DCF) analysis:

1. Set up your environment variables (see [scripts/README.md](scripts/README.md))
2. Install dependencies: `poetry install`
3. Run the analysis: `poetry run python scripts/run_dcf_analysis.py --ticker <ticker> --risk-free-rate <risk free rate> --research-report-path <path to your research report (markdown format only)>`
