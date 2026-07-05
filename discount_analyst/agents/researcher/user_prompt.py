from discount_analyst.agents.common_prompts.structured_output import (
    final_result_user_step,
)
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.surveyor.lane_context_prompt import (
    LANE_CONTEXT_QUANTITATIVE_OMISSION_NOTE,
)
from discount_analyst.agents.surveyor.schema import SurveyorLaneContext


def create_user_prompt(*, lane_context: SurveyorLaneContext) -> str:
    candidate_json = lane_context.model_dump_json(indent=2)

    return f"""
Produce a `DeepResearchReport` for the following screened candidate.

**Upstream contract:** This JSON is **worth investigating** — assume there may be a real signal, then **verify** claims with independent evidence.

**Downstream contract:** Your report must let a reader **infer what the market believes** and **where that belief could be wrong**, without you recommending a trade.

{LANE_CONTEXT_QUANTITATIVE_OMISSION_NOTE}

<SurveyorLaneContext>
{candidate_json}
</SurveyorLaneContext>

The `ticker` field uses the exchange's native format (e.g. `GLE.L` for LSE, `AVNW` for NASDAQ). Follow the symbol resolution playbook in your instructions before making any data calls.

Use the screening context as input only. Do not copy it into the output object. Populate `data_gaps_update.original_data_gaps` from the context's `data_gaps` field verbatim.

{final_result_user_step(output_type_name=DeepResearchReport.__name__)}
""".strip()
