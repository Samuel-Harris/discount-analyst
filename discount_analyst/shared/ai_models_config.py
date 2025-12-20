from enum import StrEnum
from anthropic.types.beta import BetaThinkingConfigEnabledParam
from pydantic import BaseModel, computed_field
from pydantic_ai.models.anthropic import AnthropicModelSettings
from pydantic_ai.models import ModelSettings
from pydantic_ai import UsageLimits


class ModelName(StrEnum):
    CLAUDE_OPUS_4_5 = "claude-opus-4-5"
    CLAUDE_SONNET_4_5 = "claude-sonnet-4-5"


class AIModelConfig(BaseModel):
    model_name: str
    max_tokens: int
    thinking_budget_tokens: int
    usage_limits: UsageLimits | None = None

    @property
    def model_settings(self) -> ModelSettings | None:
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


class AIModelsConfig(BaseModel):
    model_name: ModelName = ModelName.CLAUDE_OPUS_4_5

    @computed_field
    @property
    def market_analyst(self) -> AIModelConfig:
        match self.model_name:
            case ModelName.CLAUDE_OPUS_4_5:
                return AIModelConfig(
                    model_name=self.model_name,
                    max_tokens=30_000,
                    thinking_budget_tokens=16_000,
                    usage_limits=UsageLimits(tool_calls_limit=30),
                )
            case ModelName.CLAUDE_SONNET_4_5:
                return AIModelConfig(
                    model_name=self.model_name,
                    max_tokens=30_000,
                    thinking_budget_tokens=16_000,
                    usage_limits=UsageLimits(tool_calls_limit=30),
                )
            case _:
                raise ValueError(
                    f"Unsupported AI model: '{self.model_name}'. "
                    f"Supported models: {[e.value for e in ModelName]}. "
                    f"Please update the model_name to one of the supported options."
                )
