def create_profiler_user_prompt(ticker: str) -> str:
    return f"""
Ticker: {ticker}

Research this stock and populate every field of the schema. Treat it as you would any name
you have never encountered before — fresh eyes, no assumptions, no inclination toward a
particular conclusion.
""".strip()
