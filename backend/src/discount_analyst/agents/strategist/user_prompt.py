from discount_analyst.agents.common_prompts.structured_output import (
    final_result_user_step,
)
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.strategist.schema import (
    STRATEGIST_DECISION_TYPE_NAME,
    MispricingThesis,
)
from discount_analyst.agents.surveyor.lane_context_prompt import (
    LANE_CONTEXT_QUANTITATIVE_OMISSION_NOTE,
)
from discount_analyst.agents.surveyor.schema import SurveyorLaneContext


def create_user_prompt(
    *,
    lane_context: SurveyorLaneContext,
    deep_research: DeepResearchReport,
    prior_thesis: MispricingThesis | None = None,
) -> str:
    candidate_json = lane_context.model_dump_json(indent=2)
    deep_research_json = deep_research.model_dump_json(indent=2)
    prior_block = _prior_thesis_block(prior_thesis)
    keep_rule = (
        "A prior thesis is present. Emit `keep_prior` if and only if the argument, "
        "falsifiers, evaluation questions, risks, loss scenarios, and conviction "
        "are still the live claim. Emit `replace` with a full nested `MispricingThesis` "
        "if any of those must change. Do not rephrase a keep."
        if prior_thesis is not None
        else (
            "No prior thesis exists for this ticker. `keep_prior` is forbidden. "
            "You must emit `replace` with a full nested `MispricingThesis`."
        )
    )

    return f"""
You are receiving two inputs: **screening context** for the name (structured lane context JSON), and a **completed deep research report** (neutral evidence assembly). Your task is to synthesise these into a `{STRATEGIST_DECISION_TYPE_NAME}`.

**Upstream contract:** The research is **not** arguing for a trade — it may include **tensions and contradictions**. The screening block means **“worth investigating”**, not “already validated.”

**Downstream contract:** A replace thesis must be **attackable in good faith** — traceable claims, bespoke `evaluation_questions` (answerable from the last reported period plus the last trading update; not 'what will the next FY print?'), and clear “this would break me” conditions.

{LANE_CONTEXT_QUANTITATIVE_OMISSION_NOTE}

---

## Screening context (lane context)

<SurveyorLaneContext>
{candidate_json}
</SurveyorLaneContext>

---

## Deep research report

<deep_research_report>
{deep_research_json}
</deep_research_report>

{prior_block}

---

## Instructions

Begin by reading the `market_narrative` section of the deep research carefully. This is your primary input. It tells you what the market currently believes, what expectations are embedded in the price, and how the business is characterised by analysts and financial media. Your thesis is an argument that this narrative is wrong in a specific and exploitable way.

Then work through the full research report — `business_model`, `financial_profile`, `management_assessment`, and `risks` — to identify the concrete evidence that supports your argument.

As you construct the thesis, hold the following questions in mind:

- What specific error has the market made, and why? What is the mechanism of the mispricing?
- What must the market believe for the current price to be fair value — and is that belief defensible?
- What is the clearest falsification condition for this thesis? If I am wrong, how will I know?
- What is the strongest argument a skeptical analyst could make against this thesis, using the same research?
- Under what scenarios does this investment result in permanent, unrecoverable loss?

Be rigorous, be honest, and be specific. **Clarity and falsifiability matter more than completeness.**

{keep_rule}

**Action Items:**
1. First, provide your concise, human-readable reasoning. You must include the exact sentence: "This thesis hangs on [specific field/claim from the deep research]."
2. {final_result_user_step(output_type_name=STRATEGIST_DECISION_TYPE_NAME)} Use the schema from your system instructions.
""".strip()


def _prior_thesis_block(prior_thesis: MispricingThesis | None) -> str:
    if prior_thesis is None:
        return ""
    prior_json = prior_thesis.model_dump_json(indent=2)
    return f"""
---

## Prior live thesis

The following object is the last chosen live thesis for this ticker. Keep it verbatim if it is still the claim; replace it if the argument must change.

<prior_mispricing_thesis>
{prior_json}
</prior_mispricing_thesis>
""".strip()
