from pydantic import BaseModel
from pydantic_ai.models.anthropic import AnthropicModelSettings
from pydantic_ai.models import ModelSettings
from typing import Literal


class AIModelConfig(BaseModel):
    provider: Literal["anthropic"]
    model: str
    thinking_budget_tokens: int | None = None

    @property
    def model_settings(self) -> ModelSettings | None:
        if not self.thinking_budget_tokens:
            return None

        return AnthropicModelSettings(
            anthropic_thinking={
                "type": "enabled",
                "budget_tokens": self.thinking_budget_tokens,
            },
        )


class AIModelsConfig(BaseModel):
    """Configuration for AI model names used by different components."""

    assumption_maker: AIModelConfig = AIModelConfig(
        provider="anthropic",
        model="claude-opus-4-5-20251101",
        thinking_budget_tokens=10_000,
    )


ai_models_config = AIModelsConfig()
