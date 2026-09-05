import json

from pydantic import ValidationError
import pytest

from discount_analyst.agents.strategist.schema import (
    STRATEGIST_DECISION_ADAPTER,
    MispricingThesis,
    StrategistDecision,
)
from discount_analyst.application.theses import (
    KeepPriorWithoutThesisError,
    resolve_live_thesis,
)
from discount_analyst.adapters.simulation.mock_outputs import (
    mock_strategist_decision,
    mock_surveyor_candidate,
    mock_thesis,
)


def _thesis(*, argument: str = "Original argument.") -> MispricingThesis:
    return MispricingThesis(
        ticker="ABC.L",
        company_name="Abc plc",
        mispricing_type="Cyclical trough",
        market_belief="Structural decline.",
        mispricing_argument=argument,
        resolution_mechanism="Normalisation.",
        falsification_conditions=["C1", "C2", "C3"],
        thesis_risks=["Risk"],
        evaluation_questions=["Q1", "Q2", "Q3", "Q4", "Q5"],
        permanent_loss_scenarios=["PL1", "PL2"],
        conviction_level="Medium",
    )


def test_keep_prior_rejects_echoed_thesis_fields() -> None:
    with pytest.raises(ValidationError):
        StrategistDecision.model_validate(
            {"decision": "keep_prior", "thesis": _thesis().model_dump()}
        )


def test_replace_requires_nested_thesis() -> None:
    with pytest.raises(ValidationError):
        StrategistDecision.model_validate({"decision": "replace"})


def test_keep_dump_json_omits_thesis() -> None:
    dumped = json.loads(StrategistDecision(decision="keep_prior").model_dump_json())
    assert dumped == {"decision": "keep_prior"}


def test_adapter_unwraps_singleton_envelope_around_keep() -> None:
    keep = STRATEGIST_DECISION_ADAPTER.validate_python(
        {"response": {"decision": "keep_prior"}}
    )
    assert keep.decision == "keep_prior"
    assert keep.thesis is None


def test_adapter_unwraps_singleton_envelope_around_replace() -> None:
    replaced = STRATEGIST_DECISION_ADAPTER.validate_python(
        {"payload": {"decision": "replace", "thesis": _thesis().model_dump()}}
    )
    assert replaced.decision == "replace"
    assert replaced.thesis is not None
    assert replaced.thesis.ticker == "ABC.L"


def test_adapter_round_trips_keep_and_replace() -> None:
    keep = STRATEGIST_DECISION_ADAPTER.validate_json(
        StrategistDecision(decision="keep_prior").model_dump_json()
    )
    assert keep.decision == "keep_prior"
    assert keep.thesis is None
    replaced = STRATEGIST_DECISION_ADAPTER.validate_json(
        StrategistDecision(decision="replace", thesis=_thesis()).model_dump_json()
    )
    assert replaced.decision == "replace"
    assert replaced.thesis is not None
    assert replaced.thesis.ticker == "ABC.L"


def test_resolve_replace_returns_nested_thesis() -> None:
    thesis = _thesis(argument="New argument.")
    live = resolve_live_thesis(
        StrategistDecision(decision="replace", thesis=thesis), prior=_thesis()
    )
    assert live == thesis


def test_resolve_keep_copies_prior_verbatim() -> None:
    prior = _thesis()
    live = resolve_live_thesis(StrategistDecision(decision="keep_prior"), prior)
    assert live == prior
    assert live is not prior


def test_resolve_keep_without_prior_fails() -> None:
    with pytest.raises(KeepPriorWithoutThesisError, match="keep_prior is invalid"):
        resolve_live_thesis(StrategistDecision(decision="keep_prior"), None)


def test_mock_decision_keeps_when_prior_exists() -> None:
    candidate = mock_surveyor_candidate(ticker="M1.L")
    prior = mock_thesis(candidate)
    decision = mock_strategist_decision(candidate.to_lane_context(), prior)
    assert decision.decision == "keep_prior"
    assert decision.thesis is None


def test_mock_decision_replaces_without_prior() -> None:
    candidate = mock_surveyor_candidate(ticker="M1.L")
    decision = mock_strategist_decision(candidate.to_lane_context(), None)
    assert decision.decision == "replace"
    assert decision.thesis is not None
    assert decision.thesis.ticker == "M1.L"
