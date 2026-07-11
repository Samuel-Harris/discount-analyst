"""Dashboard pipeline LLM configuration for agent executions."""

from __future__ import annotations

from dataclasses import dataclass

from discount_analyst.config.settings import Settings
from discount_analyst.config.ai_models_config import AIModelsConfig
from discount_analyst.domain.model_selection.model_name import ModelName


@dataclass(frozen=True, slots=True)
class PipelineLlmConfig:
    """Resolved LLM config for one pipeline agent run (empty when mock)."""

    ai_models_config: AIModelsConfig | None
    model_name: ModelName | None


def pipeline_llm_config(settings: Settings, *, is_mock: bool) -> PipelineLlmConfig:
    """Build AIModelsConfig once; derive persisted model_name from the same object."""
    if is_mock:
        return PipelineLlmConfig(ai_models_config=None, model_name=None)
    ai_models_config = AIModelsConfig(model_name=settings.default_model)
    return PipelineLlmConfig(
        ai_models_config=ai_models_config,
        model_name=ai_models_config.model_name,
    )
