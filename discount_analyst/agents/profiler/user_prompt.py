def create_profiler_user_prompt(ticker: str) -> str:
    """Build the user message for a single-ticker Profiler run."""
    return f"""
Profile the following stock.

Ticker: {ticker}

Research this company using available financial data sources, recent filings, analyst
commentary, and financial media. Populate every field of the StockCandidate schema.

Apply the same standard you would apply to a name you had never encountered before.
""".strip()
