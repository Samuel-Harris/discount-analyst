from discount_analyst.shared.schemas.researcher import DeepResearchReport
from discount_analyst.shared.schemas.strategist import MispricingThesis
from discount_analyst.shared.schemas.surveyor import SurveyorCandidate


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

You have been provided with the full outputs of the Surveyor, Researcher, and Strategist agents. Your task is to evaluate whether the Strategist's thesis holds up against the evidence — and to deliver a clear, defensible verdict.

---

## Surveyor Candidate

<SurveyorCandidate>
{candidate_json}
</SurveyorCandidate>

---

## Deep Research Report

<DeepResearchReport>
{deep_research_json}
</DeepResearchReport>

---

## Mispricing Thesis

<MispricingThesis>
{thesis_json}
</MispricingThesis>

---

## Your Task

Work through the evaluation in the sequence defined in your instructions:

1. Answer each of the Strategist's evaluation_questions in turn, assessing the quality and weight of evidence — not merely the direction of the answer.
2. Apply the universal red flag screen across all six dimensions. The screen is thesis-agnostic. Run it regardless of how strong the thesis appears.
3. Identify any material data gaps that are load-bearing for the thesis and have not been resolved by the Researcher.
4. Deliver your thesis_verdict, verdict_rationale, caveats, and recommendation.

Your verdict must be earned by your analysis — not assumed from the Strategist's conviction level. If the thesis is "High" conviction and your assessment breaks it, say so. If the thesis is "Low" conviction and your assessment supports it, say so.

Return your output as a populated EvaluationReport JSON object.
""".strip()
