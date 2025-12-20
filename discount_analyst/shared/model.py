from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models import Model

from discount_analyst.shared.settings import settings
from discount_analyst.shared.rate_limit_client import create_rate_limit_client
from discount_analyst.shared.ai_models_config import AIModelConfig


def create_model_from_config(config: AIModelConfig, /) -> Model:
    return AnthropicModel(
        config.model_name,
        provider=AnthropicProvider(
            api_key=settings.anthropic.api_key, http_client=create_rate_limit_client()
        ),
    )
