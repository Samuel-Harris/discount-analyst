from discount_analyst.agents.surveyor.schema import SurveyorCandidate


def create_user_prompt(*, surveyor_candidate: SurveyorCandidate) -> str:
    candidate_json = surveyor_candidate.model_dump_json(indent=2)

    return f"""
Produce a `DeepResearchReport` for the following screened candidate.

**Upstream contract:** This JSON is **worth investigating** — assume there may be a real signal, then **verify** claims with independent evidence.

**Downstream contract:** Your report must let a reader **infer what the market believes** and **where that belief could be wrong**, without you recommending a trade.

<SurveyorCandidate>
{candidate_json}
</SurveyorCandidate>

Return only the `DeepResearchReport` JSON object. No preamble, no markdown.
""".strip()
