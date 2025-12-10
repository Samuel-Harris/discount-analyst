from discount_analyst.shared.data_types import StockData


def create_user_prompt(*, stock_data: StockData, research_report: str) -> str:
    return f"""
Please analyze the following company and determine the DCF valuation assumptions.

<StockData>
{stock_data.model_dump_json(indent=2)}
</StockData>

<ResearchReport>
{research_report}
</ResearchReport>

The ResearchReport above contains comprehensive analysis of the company including:
- Revenue growth trends and quality metrics
- Profitability margins and unit economics
- Market opportunity and competitive positioning
- Customer metrics (NRR, churn, cohort data)
- Management track record and execution
- Financial health and cash flow analysis
- Valuation benchmarks vs peers
- Growth catalysts and risk factors

Use this research report as your PRIMARY source for:
1. Historical revenue growth rates
2. EBIT/operating margin trends and peer benchmarks
3. Industry growth forecasts and TAM data
4. Competitive dynamics and market share
5. Customer retention and expansion metrics
6. Financial health including cash flow trends
7. Peer company comparisons for benchmarking

Additionally, use web search to supplement the research report where needed:
- Official 10-K filings for precise D&A figures from cash flow statements
- Working capital change calculations from historical cash flow statements
- Statutory tax rates for the company's jurisdiction
- Recent analyst estimates or guidance updates since the research report
- Any missing peer financial metrics not covered in the research report

Remember to:
1. Calculate current metrics from the provided StockData (current year snapshot)
2. Extract historical trends from the ResearchReport
3. Use peer benchmarks from the ResearchReport
4. Search for specific financial statement line items (D&A, working capital changes) that may not be in the research report
5. Ensure all assumptions are internally consistent
6. Output ONLY the final JSON object with no markdown formatting or explanatory text

Cross-reference the research report findings with the StockData to ensure consistency. If there are any discrepancies between the research report and StockData (e.g., different revenue figures), prioritize the StockData as it represents the most current snapshot.

Return the StockAssumptions JSON now.
""".strip()
