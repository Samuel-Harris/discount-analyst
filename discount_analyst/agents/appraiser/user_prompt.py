from discount_analyst.agents.appraiser.schema import AppraiserInput


def create_user_prompt(*, appraiser_input: AppraiserInput) -> str:
    ticker = appraiser_input.stock_candidate.ticker
    candidate_json = appraiser_input.stock_candidate.model_dump_json(indent=2)
    deep_research_json = appraiser_input.deep_research.model_dump_json(indent=2)
    thesis_json = appraiser_input.thesis.model_dump_json(indent=2)
    evaluation_json = appraiser_input.evaluation.model_dump_json(indent=2)
    rfr = appraiser_input.risk_free_rate

    return f"""
Analyze **{ticker}** and determine the DCF valuation assumptions.

**Upstream contract:** You receive **structured screening context** (`stock_candidate`), **neutral deep research** (`deep_research`), the **mispricing thesis** (`thesis`), and the Sentinel **evaluation** (`evaluation`). Screening is **“worth modelling” framing**, not verified financials — **validate** flags and gaps against filings and your own `web_search` work. The thesis and evaluation are claims and stress-test results to respect when building assumptions; they do not replace live financial facts.

**Downstream contract:** Return **inspectable** `StockData` and `StockAssumptions` — someone else should see **what you used** and **why**, without private context.

**Risk-free rate (externally supplied — do not infer or override):** {rfr} (decimal, e.g. 0.045 means 4.5%). This value is passed into the DCF after your output; state in `StockAssumptions.reasoning` only if you reference it, and **do not substitute a different rate**.

---

## Screening context

<SurveyorCandidate>
{candidate_json}
</SurveyorCandidate>

---

## Deep research report

<DeepResearchReport>
{deep_research_json}
</DeepResearchReport>

---

## Mispricing thesis

<MispricingThesis>
{thesis_json}
</MispricingThesis>

---

## Sentinel evaluation

<EvaluationReport>
{evaluation_json}
</EvaluationReport>

---

## Your task

Step 1: Find the current financial data for {ticker} (StockData).
Step 2: Determine appropriate future assumptions (StockAssumptions).

Use the JSON blocks alongside each other to:
- Use **sector and industry** from the candidate to ground **peers, competitive context, and structural economics** — do **not** label the stock “value” or “growth” or choose assumptions from a style bucket; derive projections from **evidence and the mispricing story**, not from market-style categories
- Weigh the stated rationale and key metrics (where present) against your own StockData and assumptions
- Treat red_flags and data_gaps in the candidate as hypotheses to validate or refine — not as ground truth
- Incorporate thesis conviction, falsifiable claims, and Sentinel caveats when judging projection risk — without treating prose as audited numbers
- Prefer the deep research report and live data for numbers; use the candidate block for **consistent framing** with how the name was first characterised (signals and concerns from screening, not a category label)

The DeepResearchReport contains comprehensive analysis of the company including:
- Revenue growth trends and quality metrics
- Profitability margins and unit economics
- Market opportunity and competitive positioning
- Customer metrics (NRR, churn, cohort data)
- Management track record and execution
- Financial health and cash flow analysis
- Valuation benchmarks vs peers
- Growth catalysts and risk factors

Use this structured research as your PRIMARY source for:
1. Historical revenue growth rates
2. EBIT/operating margin trends and peer benchmarks
3. Industry growth forecasts and TAM data
4. Competitive dynamics and market share
5. Customer retention and expansion metrics
6. Financial health including cash flow trends
7. Peer company comparisons for benchmarking

Additionally, use web search to supplement where needed:
- Official 10-K filings for precise D&A figures from cash flow statements
- Working capital change calculations from historical cash flow statements
- Statutory tax rates for the company's jurisdiction
- Recent analyst estimates or guidance updates since the research was produced
- Any missing peer financial metrics not covered in the research report

Remember to:
1. Calculate current metrics from the provided StockData (current year snapshot)
2. Extract historical trends from the DeepResearchReport narrative and facts
3. Use peer benchmarks from the DeepResearchReport
4. Search for specific financial statement line items (D&A, working capital changes) that may not be in the research body
5. Ensure all assumptions are internally consistent
6. Output ONLY the final JSON object with no markdown formatting or explanatory text

Cross-reference the research findings with the StockData to ensure consistency. If there are any discrepancies between the research and StockData (e.g., different revenue figures), prioritize the StockData as it represents the most current snapshot.

Return the full `AppraiserOutput` JSON (`stock_data` and `stock_assumptions`) now.
""".strip()
