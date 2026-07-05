from discount_analyst.agents.appraiser.schema import AppraiserInput, AppraiserOutput
from discount_analyst.agents.common_prompts.structured_output import (
    final_result_user_step,
)
from discount_analyst.agents.surveyor.lane_context_prompt import (
    LANE_CONTEXT_QUANTITATIVE_OMISSION_NOTE,
)


def create_user_prompt(*, appraiser_input: AppraiserInput) -> str:
    ticker = appraiser_input.lane_context.ticker
    candidate_json = appraiser_input.lane_context.model_dump_json(indent=2)
    deep_research_json = appraiser_input.deep_research.model_dump_json(indent=2)
    thesis_json = appraiser_input.thesis.model_dump_json(indent=2)
    evaluation_json = appraiser_input.evaluation.model_dump_json(indent=2)
    rfr = appraiser_input.risk_free_rate_pct

    return f"""
Analyze **{ticker}** and produce a method-agnostic intrinsic value distribution.

**Upstream contract:** You receive **structured screening context** (`lane_context`), **neutral deep research** (`deep_research`), the **mispricing thesis** (`thesis`), and the Sentinel **evaluation** (`evaluation`). Screening is **“worth modelling” framing**, not verified financials — **validate** flags and gaps against filings and your own web-search work. The thesis and evaluation are claims and stress-test results to respect when building assumptions; they do not replace live financial facts.

**Downstream contract:** Return **valuation-only** `AppraiserOutput` JSON containing:
- `valuation_distribution` with current price, expected intrinsic value, p10/p25/p50/p75/p90 intrinsic values, currency, method, and reasoning
- `methods` with exactly one primary method and at least one cross-check method
- method evidence summaries, key value drivers, downside risks, upside drivers, data quality, and caveats

Do **not** return DCF-specific `stock_data` or `stock_assumptions`. Do **not** return an investment rating or recommended action.

{LANE_CONTEXT_QUANTITATIVE_OMISSION_NOTE}

**Risk-free rate (externally supplied — do not infer or override):** {rfr} (percentage points, e.g. 4.5 means 4.5%). Use this value if you run DCF, reverse DCF, discount-rate sensitivity, or a related cross-check. If you use it, cite it in the relevant method evidence. Do not substitute a different rate.

**Valuation output convention:** All intrinsic values are **per share** in the declared currency. Express method weights as percentage points (e.g. `60.0` for 60%). Percentiles must be monotonic and `expected_intrinsic_value` must lie between p10 and p90.

---

## Screening context

<SurveyorLaneContext>
{candidate_json}
</SurveyorLaneContext>

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

Step 1: Establish current market data for {ticker}: share price, currency, market cap, share count, and any required currency conversion.
Step 2: Identify the most appropriate primary valuation method for the business and thesis.
Step 3: Use at least one cross-check method. If the evidence for a cross-check is weak, include it with clear limitations rather than omitting it.
Step 4: Triangulate the method results into a single intrinsic-value distribution.
Step 5: {final_result_user_step(output_type_name=AppraiserOutput.__name__)}

Use the JSON blocks alongside each other to:
- Use **sector and industry** from the lane context to ground **peers, competitive context, and structural economics** — do **not** label the stock “value” or “growth” or choose assumptions from a style bucket; derive projections from **evidence and the mispricing story**, not from market-style categories
- Treat red_flags and data_gaps in the lane context as hypotheses to validate or refine — not as ground truth
- Incorporate thesis conviction, falsifiable claims, and Sentinel caveats when judging valuation risk — without treating prose as audited numbers
- Prefer the deep research report and live data for numbers; use the lane context for **consistent framing** with how the name was first characterised (signals and concerns from screening, not a category label)

The DeepResearchReport contains comprehensive analysis of the company including:
- Revenue growth trends and quality metrics
- Profitability margins and unit economics
- Market opportunity and competitive positioning
- Customer metrics (NRR, churn, cohort data)
- Management track record and execution
- Financial health and cash flow analysis
- Valuation benchmarks vs peers
- Growth catalysts and risk factors

Use this structured research as a primary source for:
1. Historical revenue growth rates
2. EBIT/operating margin trends and peer benchmarks
3. Industry growth forecasts and TAM data
4. Competitive dynamics and market share
5. Customer retention and expansion metrics
6. Financial health including cash flow trends
7. Peer company comparisons for benchmarking

Additionally, use web search to supplement where needed:
- Official filings and annual reports for precise financial statement line items
- Working capital, capex, depreciation, debt, cash, and share-count details if needed for the selected method
- Statutory tax rates for the company's jurisdiction
- Recent analyst estimates or guidance updates since the research was produced
- Any missing peer financial metrics not covered in the research report
- Current market price, market cap, enterprise value, and peer multiples

Remember to:
1. State which method is primary and which methods are cross-checks
2. Extract historical trends from the DeepResearchReport narrative and facts
3. Use peer benchmarks from the DeepResearchReport and current market sources
4. Use terminal-backed calculations or `discount_analyst/valuation/toolkit` helpers where useful, but do not force the toolkit if direct calculation is clearer
5. Ensure all per-share values are internally consistent, in one declared currency, and reconciled to the current share price
6. Include concise evidence summaries and limitations for each method
7. Output ONLY the final JSON object with no markdown formatting or explanatory text

Cross-reference research findings with live market and filing data. If there are discrepancies, prefer the most recent authoritative source and note the conflict in `methods[*].evidence_summary`, `methods[*].limitations`, or `caveats`.

Return the full method-agnostic `AppraiserOutput` JSON now.
""".strip()
