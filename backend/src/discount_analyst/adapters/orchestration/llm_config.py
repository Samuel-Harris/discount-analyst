"""Dashboard pipeline LLM configuration for agent executions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import assert_never

from discount_analyst.adapters.persistence.models import AgentNameDb
from discount_analyst.config.ai_models_config import AIModelsConfig
from discount_analyst.config.settings import AgentDefaultModels, Settings
from discount_analyst.domain.model_selection.model_name import ModelName


@dataclass(frozen=True, slots=True)
class PipelineLlmConfig:
    """Resolved LLM config for one pipeline agent run (empty when mock)."""

    ai_models_config: AIModelsConfig | None
    model_name: ModelName | None


def _default_model_for(
    defaults: AgentDefaultModels, agent_name: AgentNameDb
) -> ModelName:
    match agent_name:
        case AgentNameDb.SURVEYOR:
            return defaults.surveyor
        case AgentNameDb.PROFILER:
            return defaults.profiler
        case AgentNameDb.RESEARCHER:
            return defaults.researcher
        case AgentNameDb.STRATEGIST:
            return defaults.strategist
        case AgentNameDb.SENTINEL:
            return defaults.sentinel
        case AgentNameDb.APPRAISER:
            return defaults.appraiser
        case AgentNameDb.CURATOR:
            return defaults.curator
        case _:
            assert_never(agent_name)


def pipeline_llm_config(
    settings: Settings, *, agent_name: AgentNameDb, is_mock: bool
) -> PipelineLlmConfig:
    """Build AIModelsConfig for one agent; derive persisted model_name from the same object."""
    if is_mock:
        return PipelineLlmConfig(ai_models_config=None, model_name=None)
    model_name = _default_model_for(settings.agent_default_models, agent_name)
    ai_models_config = AIModelsConfig(model_name=model_name)
    return PipelineLlmConfig(
        ai_models_config=ai_models_config,
        model_name=ai_models_config.model_name,
    )
