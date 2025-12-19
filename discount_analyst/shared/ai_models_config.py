from pydantic import BaseModel, Field
from pydantic_ai.models.anthropic import AnthropicModelSettings
from pydantic_ai.models import ModelSettings
from pydantic_ai import UsageLimits


class AIModelConfig(BaseModel):
    model_name: str
    max_tokens: int | None = None
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
            max_tokens=self.max_tokens,
            anthropic_thinking=anthropic_thinking,
            anthropic_cache_instructions="1h",
            anthropic_cache_tool_definitions="1h",
            parallel_tool_calls=True,
        )


class AIModelsConfig(BaseModel):
    assumption_maker: AIModelConfig = Field(
        default_factory=lambda: AIModelConfig(
            model_name="claude-opus-4-5",
            max_tokens=30_000,
            thinking_budget_tokens=16_000,
            usage_limits=UsageLimits(tool_calls_limit=30),
        )
    )
