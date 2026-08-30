from discount_analyst.agents.strategist.user_prompt import create_user_prompt
from discount_analyst.adapters.simulation.mock_outputs import (
    mock_deep_research,
    mock_surveyor_candidate,
    mock_thesis,
)
from discount_analyst.agents.strategist.system_prompt import SYSTEM_PROMPT


def test_user_prompt_forbids_keep_without_prior() -> None:
    candidate = mock_surveyor_candidate(ticker="ABC.L")
    prompt = create_user_prompt(
        lane_context=candidate.to_lane_context(),
        deep_research=mock_deep_research(candidate),
    )

    assert "<prior_mispricing_thesis>" not in prompt
    assert "keep_prior` is forbidden" in prompt
    assert "StrategistDecision" in prompt


def test_user_prompt_injects_prior_thesis_block() -> None:
    candidate = mock_surveyor_candidate(ticker="ABC.L")
    prior = mock_thesis(candidate)
    prompt = create_user_prompt(
        lane_context=candidate.to_lane_context(),
        deep_research=mock_deep_research(candidate),
        prior_thesis=prior,
    )

    assert "<prior_mispricing_thesis>" in prompt
    assert prior.mispricing_argument in prompt
    assert "Do not rephrase a keep" in prompt


def test_system_prompt_describes_keep_versus_replace() -> None:
    assert "keep_prior" in SYSTEM_PROMPT
    assert "StrategistDecision" in SYSTEM_PROMPT
    assert "**Do not rephrase a keep.**" in SYSTEM_PROMPT
