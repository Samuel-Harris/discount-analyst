from pydantic import BaseModel, Field
from pydantic_ai.models.anthropic import AnthropicModelSettings, AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models import ModelSettings
from pydantic_ai.models import Model

from discount_analyst.shared.config import settings


class AIModelConfig(BaseModel):
    model_name: str
    thinking_budget_tokens: int | None = None

    @property
    def model_settings(self) -> ModelSettings | None:
        if not self.thinking_budget_tokens:
            return None

        return AnthropicModelSettings(
            temperature=0,
            anthropic_thinking={
                "type": "enabled",
                "budget_tokens": self.thinking_budget_tokens,
            },
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
        )
    )
