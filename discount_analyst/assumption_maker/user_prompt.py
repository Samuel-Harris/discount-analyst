from discount_analyst.shared.data_types import StockData


def create_user_prompt(stock_data: StockData) -> str:
    return f"""
Please analyze the following company and determine the DCF valuation assumptions.

<StockData>
{stock_data.model_dump_json(indent=2)}
</StockData>

Using web search to gather historical financial data, peer benchmarks, and industry context, provide your complete analysis as a valid JSON object matching the StockAssumptions schema.

Remember to:
1. Calculate current metrics from the provided StockData
2. Search for 5-10 years of historical trends (revenue growth, margins, CapEx, D&A, working capital)
3. Identify and benchmark against 5-10 peer companies
4. Search for industry growth forecasts and macroeconomic data
5. Ensure all assumptions are internally consistent
6. Output ONLY the final JSON object with no markdown formatting or explanatory text

Return the StockAssumptions JSON now.
""".strip()
