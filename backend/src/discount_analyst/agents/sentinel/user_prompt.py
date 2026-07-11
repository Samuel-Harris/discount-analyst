from discount_analyst.agents.common_prompts.structured_output import (
    final_result_user_step,
)
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.sentinel.schema import EvaluationReport
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.surveyor.lane_context_prompt import (
    LANE_CONTEXT_QUANTITATIVE_OMISSION_NOTE,
)
from discount_analyst.agents.surveyor.schema import SurveyorLaneContext


def create_user_prompt(
    *,
    lane_context: SurveyorLaneContext,
    deep_research: DeepResearchReport,
    thesis: MispricingThesis,
) -> str:
    candidate_json = lane_context.model_dump_json(indent=2)
    deep_research_json = deep_research.model_dump_json(indent=2)
    thesis_json = thesis.model_dump_json(indent=2)

    return f"""
Evaluate the following investment candidate.

**Upstream contract:** You receive **screening context**, **neutral deep research**, and a **mispricing thesis** (with bespoke questions). The research does not endorse the thesis; the thesis does not excuse gaps in the research.

**Your task:** Stress-test the thesis against the evidence and deliver a **clear, defensible verdict**. You are **the adversary, not a validator** — earn the conclusion. Apply the epistemic, numeric, and red-flag calibration rules strictly.

{LANE_CONTEXT_QUANTITATIVE_OMISSION_NOTE}

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

## Your task

Work through the evaluation in the sequence defined in your instructions.

Your verdict must be **earned by your analysis** — not assumed from the thesis's stated conviction. If conviction is "High" and your assessment breaks the thesis, say so. If conviction is "Low" and your assessment supports the thesis, say so.

**CRITICAL:** {final_result_user_step(output_type_name=EvaluationReport.__name__)} Do NOT include conversational scaffolding or markdown outside the tool call.
""".strip()
