from discount_analyst.agents.allocator.schema import AllocatorInput, AllocatorProposal
from discount_analyst.agents.common_prompts.structured_output import (
    final_result_user_step,
)


def create_user_prompt(*, allocator_input: AllocatorInput) -> str:
    packed_json = allocator_input.model_dump_json(indent=2)
    return f"""
Construct the target portfolio from this packed allocation evidence.

**Upstream contract:** You receive one `AllocatorInput`: the current-position snapshot and one compact evidence row per completed lane. Lane ratings and `policy` are **final**. You do not re-rate names.

**Downstream contract:** Return `AllocatorProposal` with one `positions` row per input lane, required `cash`, `shared_risk_clusters`, and `portfolio_rationale`. Application code stamps current weights, company names, policy, and `source_run_id` afterwards. It will not repair your numbers.

---

## Packed input

<AllocatorInput>
{packed_json}
</AllocatorInput>

---

## Your task

1. Apply each lane's `policy` before sizing.
2. Form semantic shared-risk clusters, including supply-chain links that sector labels miss.
3. Rank investable names on rating, conviction, margin of safety, downside, reservations, and data quality.
4. Anchor on current weights; treat ranges as no-trade bands.
5. Keep any one company at or below 15% (targets and range uppers), grouping by casefolded company name.
6. Reduce weaker correlated names first. Unused capital goes to stronger independent ideas or cash — never to a weak diversifier.
7. {final_result_user_step(output_type_name=AllocatorProposal.__name__)}

Do **not** call tools. Do **not** drop tickers. Do **not** clip or normalise leftover weight.
""".strip()
