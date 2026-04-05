from discount_analyst.agents.surveyor.schema import SurveyorCandidate


def create_user_prompt(
    *,
    ticker: str,
    research_report: str,
    surveyor_candidate: SurveyorCandidate,
) -> str:
    candidate_json = surveyor_candidate.model_dump_json(indent=2)

    return f"""
Analyze **{ticker}** and determine the DCF valuation assumptions.

**Upstream contract:** You receive **structured screening context** (candidate JSON) plus a **deep research report**. Screening is **“worth modelling” framing**, not verified financials — **validate** flags and gaps against filings and your own `web_search` work.

**Downstream contract:** Return **inspectable** `StockData` and `StockAssumptions` — someone else should see **what you used** and **why**, without private context.

Step 1: Find the current financial data for {ticker} (StockData).
Step 2: Determine appropriate future assumptions (StockAssumptions).

<SurveyorCandidate>
{candidate_json}
</SurveyorCandidate>

Use the candidate JSON alongside the research report to:
- Align with the suggested value vs growth category and sector/industry framing
- Weigh the stated rationale and key metrics (where present) against your own StockData and assumptions
- Treat red_flags and data_gaps as hypotheses to validate or refine — not as ground truth
- Prefer the deep research report and live data for numbers; use the candidate block for **consistent framing** with how the name was first characterised

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
