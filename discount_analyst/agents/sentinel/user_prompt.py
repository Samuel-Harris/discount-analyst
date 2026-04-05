from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.surveyor.schema import SurveyorCandidate


def create_user_prompt(
    *,
    surveyor_candidate: SurveyorCandidate,
    deep_research: DeepResearchReport,
    thesis: MispricingThesis,
) -> str:
    candidate_json = surveyor_candidate.model_dump_json(indent=2)
    deep_research_json = deep_research.model_dump_json(indent=2)
    thesis_json = thesis.model_dump_json(indent=2)

    return f"""
Evaluate the following investment candidate.

**Upstream contract:** You receive **screening context**, **neutral deep research**, and a **mispricing thesis** (with bespoke questions). The research does not endorse the thesis; the thesis does not excuse gaps in the research.

**Your task:** Stress-test the thesis against the evidence and deliver a **clear, defensible verdict**. You are **the adversary, not a validator** — earn the conclusion.

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

## Your task

Work through the evaluation in the sequence defined in your instructions:

1. Answer each **evaluation_question** from the thesis in turn, assessing the quality and weight of evidence — not merely the direction of the answer.
2. Apply the universal red flag screen across all six dimensions. The screen is thesis-agnostic. Run it regardless of how strong the thesis appears.
3. Identify any material data gaps that are load-bearing for the thesis and remain unresolved in the research.
4. Deliver your thesis_verdict, verdict_rationale, caveats, and material_data_gaps (see schema — no separate recommendation field).

Your verdict must be **earned by your analysis** — not assumed from the thesis's stated conviction. If conviction is "High" and your assessment breaks the thesis, say so. If conviction is "Low" and your assessment supports the thesis, say so.

Return your output as a populated EvaluationReport JSON object.
""".strip()
