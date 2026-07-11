from discount_analyst.config.ai_models_config import (
    AIModelsConfig,
    DeepSeekAIModelConfig,
)
from discount_analyst.domain.model_selection.model_name import ModelName
from discount_analyst.config.provider_features import Provider, ProviderFeature


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
