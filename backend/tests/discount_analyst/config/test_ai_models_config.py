import pytest
from pydantic import ValidationError

from discount_analyst.config.ai_models_config import (
    AIModelsConfig,
    DeepSeekAIModelConfig,
    OpenAIAIModelConfig,
)
from discount_analyst.config.provider_features import Provider, ProviderFeature
from discount_analyst.domain.model_selection.model_name import ModelName


def test_deepseek_v4_pro_model_config() -> None:
    config = AIModelsConfig(model_name=ModelName.DEEPSEEK_V4_PRO)

    model = config.model

    assert isinstance(model, DeepSeekAIModelConfig)
    assert model.provider is Provider.DEEPSEEK
    assert model.model_name == "deepseek-v4-pro"
    assert model.supports_feature(ProviderFeature.MCP)
    assert model.model_settings.get("openai_reasoning_effort") == "high"
    assert model.model_settings.get("extra_body") == {"thinking": {"type": "enabled"}}


def test_deepseek_v4_flash_model_config() -> None:
    config = AIModelsConfig(model_name=ModelName.DEEPSEEK_V4_FLASH)

    model = config.model

    assert isinstance(model, DeepSeekAIModelConfig)
    assert model.provider is Provider.DEEPSEEK
    assert model.model_name == "deepseek-v4-flash"


def test_gpt_5_6_luna_model_config() -> None:
    config = AIModelsConfig(model_name=ModelName.GPT_5_6_LUNA)

    model = config.model

    assert isinstance(model, OpenAIAIModelConfig)
    assert model.provider is Provider.OPENAI
    assert model.model_name == "gpt-5.6-luna"
    assert model.supports_feature(ProviderFeature.MCP)
    assert model.model_settings.get("openai_reasoning_effort") == "high"


def test_gpt_5_6_terra_model_config() -> None:
    config = AIModelsConfig(model_name=ModelName.GPT_5_6_TERRA)

    model = config.model

    assert isinstance(model, OpenAIAIModelConfig)
    assert model.provider is Provider.OPENAI
    assert model.model_name == "gpt-5.6-terra"
    assert model.supports_feature(ProviderFeature.MCP)
    assert model.model_settings.get("openai_reasoning_effort") == "high"


def test_every_model_name_has_a_config() -> None:
    for model_name in ModelName:
        config = AIModelsConfig(model_name=model_name)
        assert config.model.model_name == model_name


def test_ai_models_config_requires_model_name() -> None:
    with pytest.raises(ValidationError):
        AIModelsConfig()  # type: ignore[call-arg]
