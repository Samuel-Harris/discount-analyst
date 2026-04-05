from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.surveyor.schema import SurveyorCandidate


def create_user_prompt(
    *,
    surveyor_candidate: SurveyorCandidate,
    deep_research: DeepResearchReport,
) -> str:
    candidate_json = surveyor_candidate.model_dump_json(indent=2)
    deep_research_json = deep_research.model_dump_json(indent=2)

    return f"""
You are receiving two inputs: **screening context** for the name (structured candidate JSON), and a **completed deep research report** (neutral evidence assembly). Your task is to synthesise these into a `MispricingThesis`.

**Upstream contract:** The research is **not** arguing for a trade — it may include **tensions and contradictions**. The screening block means **“worth investigating”**, not “already validated.”

**Downstream contract:** Your thesis must be **attackable in good faith** — traceable claims, bespoke `evaluation_questions`, and clear “this would break me” conditions.

---

## Screening context (candidate)

<surveyor_candidate>
{candidate_json}
</surveyor_candidate>

---

## Deep research report

<deep_research_report>
{deep_research_json}
</deep_research_report>

---

## Instructions

Begin by reading the `market_narrative` section of the deep research carefully. This is your primary input. It tells you what the market currently believes, what expectations are embedded in the price, and how the business is characterised by analysts and financial media. Your thesis is an argument that this narrative is wrong in a specific and exploitable way.

Then work through the full research report — `business_model`, `financial_profile`, `management`, and `risk_register` — to identify the concrete evidence that supports your argument.

As you construct the thesis, hold the following questions in mind:

- What specific error has the market made, and why? What is the mechanism of the mispricing?
- What must the market believe for the current price to be fair value — and is that belief defensible?
- What is the clearest falsification condition for this thesis? If I am wrong, how will I know?
- What is the strongest argument a skeptical analyst could make against this thesis, using the same research?
- Under what scenarios does this investment result in permanent, unrecoverable loss?

Be rigorous, be honest, and be specific. **Clarity and falsifiability matter more than completeness.**

Return a completed `MispricingThesis` object.
""".strip()
