from discount_analyst.agents.arbiter.schema import ArbiterInput


def create_user_prompt(*, arbiter_input: ArbiterInput) -> str:
    candidate_json = arbiter_input.stock_candidate.model_dump_json(indent=2)
    deep_json = arbiter_input.deep_research.model_dump_json(indent=2)
    thesis_json = arbiter_input.thesis.model_dump_json(indent=2)
    evaluation_json = arbiter_input.evaluation.model_dump_json(indent=2)
    valuation_json = arbiter_input.valuation.model_dump_json(indent=2)
    risk_free_rate = arbiter_input.risk_free_rate
    is_existing_position = arbiter_input.is_existing_position
    strategist_conviction_rating = arbiter_input.thesis.conviction_level

    return f"""
Please produce an ArbiterDecision for the following stock.

---

## Is Existing Position

<is_existing_position>
{is_existing_position}
</is_existing_position>

## Risk-Free Rate

<risk_free_rate>
{risk_free_rate}
</risk_free_rate>

---

## StockCandidate

<SurveyorCandidate>
{candidate_json}
</SurveyorCandidate>

---

## DeepResearchReport

<DeepResearchReport>
{deep_json}
</DeepResearchReport>

---

## MispricingThesis

<MispricingThesis>
{thesis_json}
</MispricingThesis>

---

## EvaluationReport

<EvaluationReport>
{evaluation_json}
</EvaluationReport>

---

## ValuationResult

<ValuationResult>
{valuation_json}
</ValuationResult>

---

Work through the sequencing gate before considering the valuation. Trace every material claim in your rationale to a specific prior output. Your conviction may not exceed the Strategist's conviction_level of {strategist_conviction_rating}.
"""
