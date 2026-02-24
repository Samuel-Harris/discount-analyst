from enum import StrEnum
from typing import Annotated, Literal

from anthropic.types.beta import BetaThinkingConfigEnabledParam
from pydantic import BaseModel, Field, computed_field
from pydantic_ai import UsageLimits
from pydantic_ai.models.anthropic import AnthropicModelSettings
from pydantic_ai.models.openai import OpenAIChatModelSettings
from pydantic_ai.settings import ModelSettings


class ModelName(StrEnum):
    CLAUDE_OPUS_4_5 = "claude-opus-4-5"
    CLAUDE_SONNET_4_5 = "claude-sonnet-4-5"
    CLAUDE_OPUS_4_6 = "claude-opus-4-6"
    CLAUDE_SONNET_4_6 = "claude-sonnet-4-6"
    GPT_5_1 = "gpt-5.1"
    GPT_5_2 = "gpt-5.2"
    GEMINI_3_PRO_PREVIEW = "gemini-3-pro-preview"
    GEMINI_3_1_PRO_PREVIEW = "gemini-3.1-pro-preview"


class BaseAIModelConfig(BaseModel):
    """Common fields shared by all provider model configs.

    Subclasses must narrow `provider` to a `Literal` type so Pydantic's
    discriminated union (`AIModelConfig`) can resolve the correct subclass.
    """

    provider: str
    model_name: str
    max_tokens: int
    usage_limits: UsageLimits | None = None


class AnthropicAIModelConfig(BaseAIModelConfig):
    """Anthropic model config with thinking and cache settings."""

    provider: Literal["anthropic"] = "anthropic"
    thinking_budget_tokens: int

    @property
    def model_settings(self) -> AnthropicModelSettings:
        anthropic_thinking: BetaThinkingConfigEnabledParam = {
            "type": "enabled",
            "budget_tokens": self.thinking_budget_tokens,
        }
        return AnthropicModelSettings(
            temperature=1,
            max_tokens=self.max_tokens,
            anthropic_thinking=anthropic_thinking,
            anthropic_cache_instructions="1h",
            anthropic_cache_tool_definitions="1h",
            parallel_tool_calls=True,
        )


class OpenAIAIModelConfig(BaseAIModelConfig):
    """OpenAI model config with flex service tier."""

    provider: Literal["openai"] = "openai"

    @property
    def model_settings(self) -> OpenAIChatModelSettings:
        return OpenAIChatModelSettings(
            temperature=1,
            max_tokens=self.max_tokens,
            openai_service_tier="flex",
            parallel_tool_calls=True,
        )


class GoogleAIModelConfig(BaseAIModelConfig):
    """Google model config (uses base ModelSettings; Google has implicit caching)."""

    provider: Literal["google"] = "google"

    @property
    def model_settings(self) -> ModelSettings:
        return ModelSettings(
            temperature=1,
            max_tokens=self.max_tokens,
        )


AIModelConfig = Annotated[
    AnthropicAIModelConfig | OpenAIAIModelConfig | GoogleAIModelConfig,
    Field(discriminator="provider"),
]


def _anthropic_market_analyst(model_name: ModelName) -> AnthropicAIModelConfig:
    return AnthropicAIModelConfig(
        model_name=model_name,
        max_tokens=30_000,
        thinking_budget_tokens=16_000,
        usage_limits=UsageLimits(tool_calls_limit=30),
    )


def _openai_market_analyst(model_name: ModelName) -> OpenAIAIModelConfig:
    return OpenAIAIModelConfig(
        model_name=model_name,
        max_tokens=30_000,
        usage_limits=UsageLimits(tool_calls_limit=30),
    )


def _google_market_analyst(model_name: ModelName) -> GoogleAIModelConfig:
    return GoogleAIModelConfig(
        model_name=model_name,
        max_tokens=30_000,
        usage_limits=UsageLimits(tool_calls_limit=30),
    )


class AIModelsConfig(BaseModel):
    model_name: ModelName = ModelName.CLAUDE_OPUS_4_5

    @computed_field
    @property
    def market_analyst(self) -> AIModelConfig:
        match self.model_name:
            case ModelName.CLAUDE_OPUS_4_5 | ModelName.CLAUDE_SONNET_4_5:
                return _anthropic_market_analyst(self.model_name)
            case ModelName.CLAUDE_OPUS_4_6 | ModelName.CLAUDE_SONNET_4_6:
                return _anthropic_market_analyst(self.model_name)
            case ModelName.GPT_5_1 | ModelName.GPT_5_2:
                return _openai_market_analyst(self.model_name)
            case ModelName.GEMINI_3_PRO_PREVIEW | ModelName.GEMINI_3_1_PRO_PREVIEW:
                return _google_market_analyst(self.model_name)
            case _:
                raise ValueError(
                    f"Unsupported AI model: '{self.model_name}'. "
                    f"Supported models: {[e.value for e in ModelName]}. "
                    "Please update the model_name to one of the supported options."
                )
