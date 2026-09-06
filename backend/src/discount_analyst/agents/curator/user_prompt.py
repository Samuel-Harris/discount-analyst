from discount_analyst.agents.curator.schema import CuratorInput, CuratorProposal
from discount_analyst.agents.common_prompts.structured_output import (
    final_result_user_step,
)


def create_user_prompt(*, curator_input: CuratorInput) -> str:
    packed_json = curator_input.model_dump_json(indent=2)
    return f"""
Construct the target portfolio from this packed allocation evidence.

**Upstream contract:** You receive one `CuratorInput`: the current-position snapshot and one compact evidence row per valued lane. Each lane carries a `live_thesis` plus Researcher, Strategist, Sentinel, and Appraiser memos. You do not re-rate names or edit theses. Your weights are the recommendation.

**Downstream contract:** Return `CuratorProposal` with one `positions` row per input lane, required `cash`, `shared_risk_clusters`, and `portfolio_rationale`. Application code stamps current weights, company names, `source_run_id`, and derived actions afterwards. It will not repair your numbers.

---

## Packed input

<CuratorInput>
{packed_json}
</CuratorInput>

---

## Your task

1. Form semantic shared-risk clusters from `live_thesis` mechanisms as well as sector labels, including supply-chain links that sector strings miss.
2. Rank names on whether their live theses are independent ideas, then conviction, margin of safety, downside, Sentinel labels, and data quality.
3. Anchor on current weights; treat ranges as no-trade bands.
4. You may size any weight on any packed lane, including adding to holdings and initiating new names, including 0%. Cash is valid.
5. Keep any one company at or below 15% (targets and range uppers), grouping by casefolded company name.
6. Reduce weaker correlated names first. Unused capital goes to stronger independent ideas or cash — never to a weak diversifier.
7. {final_result_user_step(output_type_name=CuratorProposal.__name__)}

Do **not** drop tickers. Do **not** clip or normalise leftover weight.
""".strip()
