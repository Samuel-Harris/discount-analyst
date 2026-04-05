from discount_analyst.agents.surveyor.schema import SurveyorCandidate


def create_user_prompt(*, surveyor_candidate: SurveyorCandidate) -> str:
    candidate_json = surveyor_candidate.model_dump_json(indent=2)

    return f"""
Produce a `DeepResearchReport` for the following Surveyor candidate.

<SurveyorCandidate>
{candidate_json}
</SurveyorCandidate>

Return only the `DeepResearchReport` JSON object. No preamble, no markdown.
""".strip()
