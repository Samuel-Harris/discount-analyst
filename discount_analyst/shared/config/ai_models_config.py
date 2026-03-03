from enum import StrEnum
from typing import Annotated, Literal

from anthropic.types.beta import BetaThinkingConfigEnabledParam
from pydantic import BaseModel, Field, computed_field
from pydantic_ai import UsageLimits
from pydantic_ai.models.anthropic import AnthropicModelSettings
from google.genai.types import ThinkingConfigDict
from pydantic_ai.models.google import GoogleModelSettings
from pydantic_ai.models.openai import OpenAIResponsesModelSettings


_MAX_TOOL_CALLS = 60
_MAX_TOKENS = 30_000
_MAX_THINKING_BUDGET_TOKENS = 16_000

_ANTHROPIC_REASONING_EFFORT = "high"
_OPENAI_REASONING_EFFORT = "high"


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
    """Anthropic model config with thinking, cache, and effort settings.

    Set `thinking_budget_tokens` for older models (4.5) that use fixed-budget extended thinking
    (`type: "enabled"`).  Leave it as `None` for 4.6+ models, which use adaptive thinking
    (`type: "adaptive"`) — Anthropic's recommended mode for Opus 4.6 and Sonnet 4.6.

    Set `effort` for 4.6+ adaptive models to cap output quality vs. cost
    (`"low"` / `"medium"` / `"high"` / `"max"`). When `None` the model decides its own effort.
    """

    provider: Literal["anthropic"] = "anthropic"
    thinking_budget_tokens: int | None = None
    cache_messages: bool = True
    effort: Literal["low", "medium", "high", "max"] | None = None

    @property
    def model_settings(self) -> AnthropicModelSettings:
        if self.thinking_budget_tokens is not None:
            anthropic_thinking: BetaThinkingConfigEnabledParam = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget_tokens,
            }
        else:
            # "adaptive" is accepted by the Anthropic API for 4.6+ models but is not
            # yet present in the SDK's BetaThinkingConfigParam TypedDict union.
            anthropic_thinking = {"type": "adaptive"}  # type: ignore[assignment]

        return AnthropicModelSettings(
            temperature=1,
            max_tokens=self.max_tokens,
            anthropic_thinking=anthropic_thinking,
            anthropic_cache_instructions="1h",
            anthropic_cache_tool_definitions="1h",
            anthropic_cache_messages="5m" if self.cache_messages else False,
            parallel_tool_calls=True,
            anthropic_effort=self.effort,
        )


class OpenAIAIModelConfig(BaseAIModelConfig):
    """OpenAI model config with flex service tier, 24h prompt caching, and privacy settings.

    Set `reasoning_effort` for reasoning models (e.g. o-series, GPT-5.x) to trade cost for
    quality (`"low"` / `"medium"` / `"high"`). When `None` the model's default is used.
    """

    provider: Literal["openai"] = "openai"
    reasoning_effort: Literal["low", "medium", "high"] | None = None

    @property
    def model_settings(self) -> OpenAIResponsesModelSettings:
        settings = OpenAIResponsesModelSettings(
            max_tokens=self.max_tokens,
            openai_service_tier="flex",
            parallel_tool_calls=True,
            openai_prompt_cache_retention="24h",
            openai_store=False,
        )
        if self.reasoning_effort is not None:
            settings["openai_reasoning_effort"] = self.reasoning_effort
        return settings


class GoogleAIModelConfig(BaseAIModelConfig):
    """Google model config with explicit thinking budget.

    Set `thinking_budget_tokens` to cap Gemini 3's reasoning cost. Without a budget the model
    uses its default thinking behaviour, which has no cost-saving guarantee (unlike Anthropic's
    explicit cache, Gemini's *implicit* caching does not guarantee savings — use
    `google_cached_content` at call time via model_settings for a guaranteed discount).
    """

    provider: Literal["google"] = "google"
    thinking_budget_tokens: int | None = None

    @property
    def model_settings(self) -> GoogleModelSettings:
        settings = GoogleModelSettings(
            temperature=1,
            max_tokens=self.max_tokens,
        )
        if self.thinking_budget_tokens is not None:
            settings["google_thinking_config"] = ThinkingConfigDict(
                thinking_budget=self.thinking_budget_tokens
            )
        return settings


AIModelConfig = Annotated[
    AnthropicAIModelConfig | OpenAIAIModelConfig | GoogleAIModelConfig,
    Field(discriminator="provider"),
]


class AIModelsConfig(BaseModel):
    model_name: ModelName = ModelName.CLAUDE_OPUS_4_5
    cache_messages: bool = True

    @computed_field
    @property
    def model(self) -> AIModelConfig:
        match self.model_name:
            case ModelName.CLAUDE_OPUS_4_6 | ModelName.CLAUDE_SONNET_4_6:
                return AnthropicAIModelConfig(
                    model_name=self.model_name,
                    max_tokens=_MAX_TOKENS,
                    usage_limits=UsageLimits(tool_calls_limit=_MAX_TOOL_CALLS),
                    cache_messages=self.cache_messages,
                    effort=_ANTHROPIC_REASONING_EFFORT,
                )
            case ModelName.CLAUDE_OPUS_4_5 | ModelName.CLAUDE_SONNET_4_5:
                return AnthropicAIModelConfig(
                    model_name=self.model_name,
                    max_tokens=_MAX_TOKENS,
                    thinking_budget_tokens=_MAX_THINKING_BUDGET_TOKENS,
                    usage_limits=UsageLimits(tool_calls_limit=_MAX_TOOL_CALLS),
                    cache_messages=self.cache_messages,
                )
            case ModelName.GPT_5_1 | ModelName.GPT_5_2:
                return OpenAIAIModelConfig(
                    model_name=self.model_name,
                    max_tokens=_MAX_TOKENS,
                    usage_limits=UsageLimits(tool_calls_limit=_MAX_TOOL_CALLS),
                    reasoning_effort=_OPENAI_REASONING_EFFORT,
                )
            case ModelName.GEMINI_3_PRO_PREVIEW | ModelName.GEMINI_3_1_PRO_PREVIEW:
                return GoogleAIModelConfig(
                    model_name=self.model_name,
                    max_tokens=_MAX_TOKENS,
                    thinking_budget_tokens=_MAX_THINKING_BUDGET_TOKENS,
                    usage_limits=UsageLimits(tool_calls_limit=_MAX_TOOL_CALLS),
                )
            case _:
                raise ValueError(
                    f"Unsupported AI model: '{self.model_name}'. "
                    f"Supported models: {[e.value for e in ModelName]}. "
                    "Please update the model_name to one of the supported options."
                )
