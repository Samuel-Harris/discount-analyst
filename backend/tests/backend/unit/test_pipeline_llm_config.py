"""Unit tests for per-agent pipeline LLM resolution."""

from __future__ import annotations

import pytest

from discount_analyst.adapters.orchestration.llm_config import pipeline_llm_config
from discount_analyst.adapters.persistence.models import AgentNameDb
from discount_analyst.config.settings import AgentDefaultModels
from discount_analyst.config.testing_settings import dashboard_settings_for_tests
from discount_analyst.domain.model_selection.model_name import ModelName


def test_agent_default_model_fields_match_agent_name_db() -> None:
    assert set(AgentDefaultModels.model_fields) == {name.value for name in AgentNameDb}


def test_pipeline_llm_config_mock_is_none() -> None:
    settings = dashboard_settings_for_tests()
    llm = pipeline_llm_config(settings, agent_name=AgentNameDb.CURATOR, is_mock=True)
    assert llm.ai_models_config is None
    assert llm.model_name is None


@pytest.mark.parametrize(
    ("agent_name", "expected"),
    [
        (AgentNameDb.SURVEYOR, ModelName.GPT_5_6_LUNA),
        (AgentNameDb.PROFILER, ModelName.GPT_5_6_LUNA),
        (AgentNameDb.RESEARCHER, ModelName.GPT_5_6_LUNA),
        (AgentNameDb.STRATEGIST, ModelName.GPT_5_6_LUNA),
        (AgentNameDb.SENTINEL, ModelName.GPT_5_6_LUNA),
        (AgentNameDb.APPRAISER, ModelName.GPT_5_6_LUNA),
        (AgentNameDb.CURATOR, ModelName.GPT_5_6_TERRA),
    ],
)
def test_pipeline_llm_config_uses_baked_in_agent_default(
    agent_name: AgentNameDb, expected: ModelName
) -> None:
    settings = dashboard_settings_for_tests()
    llm = pipeline_llm_config(settings, agent_name=agent_name, is_mock=False)
    assert llm.model_name is expected
    assert llm.ai_models_config is not None
    assert llm.ai_models_config.model_name is expected
