"""Tests for singleton ``final_result`` envelope unwrapping."""

from types import SimpleNamespace
from typing import cast

import pytest
from pydantic import BaseModel, TypeAdapter
from pydantic_ai import ToolOutput
from pydantic_ai.models.test import TestModel

from discount_analyst.agents.runtime import agent_factory
from discount_analyst.agents.runtime.agent_factory import AgentSpec, create_agent
from discount_analyst.agents.runtime.agent_names import AgentName
from discount_analyst.agents.runtime.structured_output_unwrap import (
    SINGLETON_ENVELOPE_KEYS,
    unwrap_singleton_output_envelope,
)
from discount_analyst.agents.sentinel.schema import (
    EvaluationReport,
    OverallRedFlagVerdict,
    QuestionAssessment,
    RedFlagScreen,
    ThesisVerdict,
)
from discount_analyst.config.ai_models_config import AIModelConfig, AIModelsConfig
from discount_analyst.domain.model_selection.model_name import ModelName


class _TinyReport(BaseModel):
    ticker: str
    company_name: str
    note: str = ""


@pytest.mark.parametrize("envelope_key", sorted(SINGLETON_ENVELOPE_KEYS))
def test_unwrap_singleton_output_envelope_flattens_each_envelope_key(
    envelope_key: str,
) -> None:
    inner = {"ticker": "FLXS", "company_name": "Flexsteel Industries"}
    assert unwrap_singleton_output_envelope({envelope_key: inner}) == inner


def test_unwrap_singleton_output_envelope_leaves_flat_object_unchanged() -> None:
    flat = {"ticker": "FLXS", "company_name": "Flexsteel Industries"}
    assert unwrap_singleton_output_envelope(flat) is flat


def test_unwrap_singleton_output_envelope_leaves_non_singleton_unchanged() -> None:
    two_keys = {"payload": {"ticker": "FLXS"}, "extra": 1}
    assert unwrap_singleton_output_envelope(two_keys) is two_keys


def test_unwrap_singleton_output_envelope_leaves_non_dict_inner_unchanged() -> None:
    nested_string = {"payload": "FLXS"}
    assert unwrap_singleton_output_envelope(nested_string) is nested_string


def test_tiny_report_validates_unwrapped_payload() -> None:
    nested = {"payload": {"ticker": "FLXS", "company_name": "Flexsteel Industries"}}
    report = _TinyReport.model_validate(unwrap_singleton_output_envelope(nested))
    assert report.ticker == "FLXS"
    assert report.company_name == "Flexsteel Industries"


def _flxs_evaluation_fields() -> dict[str, object]:
    return EvaluationReport(
        ticker="FLXS",
        company_name="Flexsteel Industries",
        question_assessments=[
            QuestionAssessment(
                question="Q1",
                evidence="E",
                verdict="Supports thesis",
                confidence="High",
            )
        ],
        red_flag_screen=RedFlagScreen(
            governance_concerns="",
            balance_sheet_stress="",
            customer_or_supplier_concentration="",
            accounting_quality="",
            related_party_transactions="",
            litigation_or_regulatory_risk="",
            overall_red_flag_verdict=OverallRedFlagVerdict.CLEAR,
        ),
        thesis_verdict=ThesisVerdict.INTACT_PROCEED_TO_VALUATION,
        verdict_rationale="Proceed.",
        material_data_gaps="",
        caveats=[],
    ).model_dump(mode="json")


def test_create_agent_final_result_schema_stays_flat_and_unwraps_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_create_model_from_config(_config: AIModelConfig) -> TestModel:
        return TestModel()

    def fake_agent(**kwargs: object) -> SimpleNamespace:
        captured["output_type"] = kwargs["output_type"]
        return SimpleNamespace(name=kwargs.get("name"))

    monkeypatch.setattr(
        agent_factory,
        "create_model_from_config",
        fake_create_model_from_config,
    )
    monkeypatch.setattr(agent_factory, "Agent", fake_agent)

    create_agent(
        spec=AgentSpec(
            name=AgentName.SENTINEL,
            output_type=EvaluationReport,
            system_prompt="test",
        ),
        ai_models_config=AIModelsConfig(model_name=ModelName.DEEPSEEK_V4_PRO),
        enable_web_research_tools=False,
        use_mcp_financial_data=False,
    )

    registered = captured["output_type"]
    assert isinstance(registered, ToolOutput)
    maybe_output = getattr(cast(object, registered), "output")
    assert isinstance(maybe_output, type)
    assert issubclass(maybe_output, EvaluationReport)
    adapter = TypeAdapter(maybe_output)
    properties = adapter.json_schema()["properties"]
    assert "ticker" in properties
    assert "payload" not in properties
    assert "response" not in properties
    assert "payload" not in EvaluationReport.model_fields

    report = adapter.validate_python({"payload": _flxs_evaluation_fields()})
    assert isinstance(report, EvaluationReport)
    assert report.ticker == "FLXS"
    assert report.company_name == "Flexsteel Industries"
