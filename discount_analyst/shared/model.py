from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider

from discount_analyst.shared.ai_models_config import (
    AIModelConfig,
    AnthropicAIModelConfig,
    GoogleAIModelConfig,
    OpenAIAIModelConfig,
)
from discount_analyst.shared.rate_limit_client import create_rate_limit_client
from discount_analyst.shared.settings import settings


def create_model_from_config(config: AIModelConfig, /) -> Model:
    match config:
        case AnthropicAIModelConfig():
            return AnthropicModel(
                config.model_name,
                provider=AnthropicProvider(
                    api_key=settings.anthropic.api_key,
                    http_client=create_rate_limit_client(),
                ),
            )
        case OpenAIAIModelConfig():
            return OpenAIChatModel(
                config.model_name,
                provider=OpenAIProvider(
                    api_key=settings.openai.api_key,
                    http_client=create_rate_limit_client(),
                ),
            )
        case GoogleAIModelConfig():
            return GoogleModel(
                config.model_name,
                provider=GoogleProvider(
                    api_key=settings.google.api_key,
                    http_client=create_rate_limit_client(),
                ),
            )
