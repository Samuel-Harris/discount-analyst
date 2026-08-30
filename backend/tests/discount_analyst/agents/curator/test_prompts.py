from datetime import date

from discount_analyst.agents.curator.schema import CuratorInput
from discount_analyst.agents.curator.user_prompt import create_user_prompt
from discount_analyst.domain.allocations.snapshot import CurrentPortfolioSnapshot


def test_user_prompt_embeds_packed_input_and_forbids_tools() -> None:
    packed = CuratorInput(
        allocation_date=date(2026, 8, 30),
        snapshot=CurrentPortfolioSnapshot(
            as_of=date(2026, 8, 30),
            positions=(),
            cash_weight_pct=100.0,
        ),
        lanes=(),
    )

    prompt = create_user_prompt(curator_input=packed)

    assert "<CuratorInput>" in prompt
    assert "Do **not** call tools" in prompt
    assert "CuratorProposal" in prompt
    assert "live_thesis" in prompt
    assert "independent ideas" in prompt
    assert packed.model_dump_json(indent=2) in prompt
