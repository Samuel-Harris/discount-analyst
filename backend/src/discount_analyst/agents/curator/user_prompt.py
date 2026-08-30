from discount_analyst.agents.curator.schema import CuratorInput, CuratorProposal
from discount_analyst.agents.common_prompts.structured_output import (
    final_result_user_step,
)


def create_user_prompt(*, curator_input: CuratorInput) -> str:
    packed_json = curator_input.model_dump_json(indent=2)
    return f"""
Construct the target portfolio from this packed allocation evidence.

**Upstream contract:** You receive one `CuratorInput`: the current-position snapshot and one compact evidence row per completed lane. Each lane may carry a `live_thesis` (required except an optional prior on data-quality rejection). Lane ratings and `policy` are **final**. You do not re-rate names or edit theses.

**Downstream contract:** Return `CuratorProposal` with one `positions` row per input lane, required `cash`, `shared_risk_clusters`, and `portfolio_rationale`. Application code stamps current weights, company names, policy, and `source_run_id` afterwards. It will not repair your numbers.

---

## Packed input

<CuratorInput>
{packed_json}
</CuratorInput>

---

## Your task

1. Apply each lane's `policy` before sizing.
2. Form semantic shared-risk clusters from `live_thesis` mechanisms as well as sector labels, including supply-chain links that sector strings miss.
3. Rank investable names on whether their live theses are independent ideas, then rating, conviction, margin of safety, downside, reservations, and data quality.
4. Anchor on current weights; treat ranges as no-trade bands.
5. Keep any one company at or below 15% (targets and range uppers), grouping by casefolded company name.
6. Reduce weaker correlated names first. Unused capital goes to stronger independent ideas or cash — never to a weak diversifier.
7. {final_result_user_step(output_type_name=CuratorProposal.__name__)}

Do **not** call tools. Do **not** drop tickers. Do **not** clip or normalise leftover weight.
""".strip()
