from pydantic import BaseModel, Field
from pydantic_ai.models.anthropic import AnthropicModelSettings, AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models import ModelSettings, Model
from pydantic_ai import UsageLimits

from discount_analyst.shared.config import settings


class AIModelConfig(BaseModel):
    model_name: str
    thinking_budget_tokens: int | None = None
    usage_limits: UsageLimits | None = None

    @property
    def model_settings(self) -> ModelSettings | None:
        anthropic_thinking = (
            {
                "type": "enabled",
                "budget_tokens": self.thinking_budget_tokens,
            }
            if self.thinking_budget_tokens
            else None
        )

        return AnthropicModelSettings(
            temperature=1,
            anthropic_thinking=anthropic_thinking,
            anthropic_cache_instructions="1h",
            anthropic_cache_tool_definitions="1h",
        )

    @property
    def model(self) -> Model:
        return AnthropicModel(
            self.model_name,
            provider=AnthropicProvider(api_key=settings.anthropic.api_key),
        )


class AIModelsConfig(BaseModel):
    assumption_maker: AIModelConfig = Field(
        default_factory=lambda: AIModelConfig(
            model_name="claude-opus-4-5",
            thinking_budget_tokens=10_000,
            usage_limits=UsageLimits(tool_calls_limit=30),
        )
    )
