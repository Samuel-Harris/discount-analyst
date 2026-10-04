import pytest
from pydantic import ValidationError

from discount_analyst.config.ai_models_config import (
    AIModelsConfig,
    AnthropicAIModelConfig,
    DeepSeekAIModelConfig,
    OpenAIAIModelConfig,
)
from discount_analyst.config.provider_features import Provider, ProviderFeature
from discount_analyst.domain.model_selection.model_name import ModelName


def test_deepseek_v4_pro_model_config() -> None:
    config = AIModelsConfig(model_name=ModelName.DEEPSEEK_V4_PRO)

    model = config.pydantic_ai_model

    assert isinstance(model, DeepSeekAIModelConfig)
    assert model.provider is Provider.DEEPSEEK
    assert model.model_name == "deepseek-v4-pro"
    assert model.supports_feature(ProviderFeature.MCP)
    assert model.max_concurrent_agents == 1
    assert model.model_settings.get("openai_reasoning_effort") == "high"
    assert model.model_settings.get("extra_body") == {"thinking": {"type": "enabled"}}


def test_deepseek_v4_flash_model_config() -> None:
    config = AIModelsConfig(model_name=ModelName.DEEPSEEK_V4_FLASH)

    model = config.pydantic_ai_model

    assert isinstance(model, DeepSeekAIModelConfig)
    assert model.provider is Provider.DEEPSEEK
    assert model.model_name == "deepseek-v4-flash"


def test_gpt_5_6_luna_model_config() -> None:
    config = AIModelsConfig(model_name=ModelName.GPT_5_6_LUNA)

    model = config.pydantic_ai_model

    assert isinstance(model, OpenAIAIModelConfig)
    assert model.provider is Provider.OPENAI
    assert model.model_name == "gpt-5.6-luna"
    assert model.max_concurrent_agents == 1
    assert model.reasoning_mode == "standard"
    assert model.supports_feature(ProviderFeature.MCP)
    assert model.model_settings.get("openai_reasoning_effort") == "high"
    assert model.model_settings.get("openai_reasoning_mode") == "standard"


def test_gpt_6_luna_model_config() -> None:
    config = AIModelsConfig(model_name=ModelName.GPT_6_LUNA)

    model = config.pydantic_ai_model

    assert isinstance(model, OpenAIAIModelConfig)
    assert model.provider is Provider.OPENAI
    assert model.model_name == "gpt-6-luna"
    assert model.max_concurrent_agents == 20
    assert model.reasoning_mode == "standard"
    assert model.supports_feature(ProviderFeature.MCP)
    assert model.model_settings.get("openai_reasoning_effort") == "high"
    assert model.model_settings.get("openai_reasoning_mode") == "standard"


def test_gpt_6_1_sol_model_config() -> None:
    config = AIModelsConfig(model_name=ModelName.GPT_6_1_SOL)

    model = config.pydantic_ai_model

    assert isinstance(model, OpenAIAIModelConfig)
    assert model.provider is Provider.OPENAI
    assert model.model_name == "gpt-6.1-sol"
    assert model.max_concurrent_agents == 5
    assert model.reasoning_mode == "pro"
    assert model.supports_feature(ProviderFeature.MCP)
    assert model.model_settings.get("openai_reasoning_effort") == "high"
    assert model.model_settings.get("openai_reasoning_mode") == "pro"


def test_gpt_5_6_terra_model_config() -> None:
    config = AIModelsConfig(model_name=ModelName.GPT_5_6_TERRA)

    model = config.pydantic_ai_model

    assert isinstance(model, OpenAIAIModelConfig)
    assert model.provider is Provider.OPENAI
    assert model.model_name == "gpt-5.6-terra"
    assert model.max_concurrent_agents == 1
    assert model.reasoning_mode == "standard"
    assert model.supports_feature(ProviderFeature.MCP)
    assert model.model_settings.get("openai_reasoning_effort") == "high"
    assert model.model_settings.get("openai_reasoning_mode") == "standard"


def test_anthropic_4_6_uses_adaptive_effort() -> None:
    model = AIModelsConfig(model_name=ModelName.CLAUDE_OPUS_4_6).pydantic_ai_model

    assert isinstance(model, AnthropicAIModelConfig)
    assert model.effort == "high"
    assert model.thinking_budget_tokens is None
    assert model.max_concurrent_agents == 1
    assert model.model_settings.get("anthropic_effort") == "high"


def test_anthropic_budget_models_clear_adaptive_effort() -> None:
    for model_name in (
        ModelName.CLAUDE_OPUS_4_5,
        ModelName.CLAUDE_SONNET_4_5,
        ModelName.CLAUDE_HAIKU_4_6,
    ):
        model = AIModelsConfig(model_name=model_name).pydantic_ai_model
        assert isinstance(model, AnthropicAIModelConfig)
        assert model.effort is None
        assert model.thinking_budget_tokens == 16_000
        assert model.max_concurrent_agents == 1


def test_every_model_name_has_a_config() -> None:
    for model_name in ModelName:
        config = AIModelsConfig(model_name=model_name)
        assert config.pydantic_ai_model.model_name == model_name


def test_ai_models_config_requires_model_name() -> None:
    with pytest.raises(ValidationError):
        AIModelsConfig()  # type: ignore[call-arg]
