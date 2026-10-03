from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any, Literal, assert_never

from anthropic.types.beta import BetaThinkingConfigEnabledParam
from discount_analyst.config.model_gate import (
    ProcessModelGate,
    bound_stream_attempt,
    process_model_gate,
)
from discount_analyst.config.provider_features import (
    PROVIDERS_BY_FEATURE,
    Provider,
    ProviderFeature,
)
from discount_analyst.config.rate_limit_client import create_rate_limit_client
from discount_analyst.config.settings import settings
from discount_analyst.domain.model_selection.model_name import ModelName
from google.genai.types import ThinkingConfigDict
from pydantic import BaseModel, Field, computed_field
from pydantic_ai import RunContext, UsageLimits
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import Model, ModelRequestParameters, StreamedResponse
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.models.openai import (
    OpenAIChatModel,
    OpenAIChatModelSettings,
    OpenAIResponsesModel,
    OpenAIResponsesModelSettings,
)
from pydantic_ai.models.wrapper import WrapperModel
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import RequestUsage

_MAX_TOOL_CALLS = 60
_MAX_TOKENS = 30_000
_USAGE_LIMITS = UsageLimits(tool_calls_limit=_MAX_TOOL_CALLS)
_MAX_THINKING_BUDGET_TOKENS = 16_000
_OPENAI_COMPACTION_THRESHOLD_TOKENS = 200_000

_ANTHROPIC_REASONING_EFFORT = "high"
_OPENAI_REASONING_EFFORT = "high"
_DEEPSEEK_REASONING_EFFORT = "high"
_LONG_RUN_TIMEOUT_SECONDS = 1200


class AdmittedModel(WrapperModel):
    """Provider model that takes one process-gate slot per model call.

    On a provider rate limit the gate is armed before the slot is released,
    so another workflow cannot acquire in that gap.
    """

    def __init__(self, wrapped: Model, gate: ProcessModelGate) -> None:
        super().__init__(wrapped)
        self.gate = gate

    @asynccontextmanager
    async def _segment(self) -> AsyncGenerator[None]:
        await self.gate.acquire(f"model:{self.model_name}")
        try:
            yield
        except Exception as exc:
            self.gate.arm(exc, attempt=bound_stream_attempt())
            raise
        finally:
            self.gate.release()

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        async with self._segment():
            return await self.wrapped.request(
                messages, model_settings, model_request_parameters
            )

    async def count_tokens(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> RequestUsage:
        async with self._segment():
            return await self.wrapped.count_tokens(
                messages, model_settings, model_request_parameters
            )

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncGenerator[StreamedResponse]:
        async with self._segment():
            async with self.wrapped.request_stream(
                messages,
                model_settings,
                model_request_parameters,
                run_context,
            ) as response_stream:
                yield response_stream


class BaseAIModelConfig[P: Provider](BaseModel, ABC):
    """Common fields shared by all provider model configs.

    Each concrete config specializes ``P`` to ``Literal[Provider.X]`` so the ``provider``
    field is a discriminant for ``AIModelConfig`` without invariant override errors.
    """

    provider: P
    model_name: str
    max_tokens: int
    usage_limits: UsageLimits
    max_concurrent_agents: int = Field(default=1, ge=1)

    def supports_feature(self, feature: ProviderFeature) -> bool:
        return self.provider in PROVIDERS_BY_FEATURE[feature]

    @abstractmethod
    def to_model(self) -> AdmittedModel:
        """Return the provider model on this config's process gate."""


class AnthropicAIModelConfig(BaseAIModelConfig[Literal[Provider.ANTHROPIC]]):
    """Anthropic model config with thinking, cache, and effort settings.

    Set `thinking_budget_tokens` for older models (4.5) that use fixed-budget extended thinking
    (`type: "enabled"`).  Leave it as `None` for 4.6+ models, which use adaptive thinking
    (`type: "adaptive"`) — Anthropic's recommended mode for Opus 4.6 and Sonnet 4.6.

    Set `effort` for 4.6+ adaptive models to cap output quality vs. cost
    (`"low"` / `"medium"` / `"high"` / `"max"`). When `None` the model decides its own effort.
    """

    provider: Literal[Provider.ANTHROPIC] = Provider.ANTHROPIC
    thinking_budget_tokens: int | None = None
    cache_messages: bool = True
    effort: Literal["low", "medium", "high", "max"] | None = _ANTHROPIC_REASONING_EFFORT

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

    def _provider_model(self) -> AnthropicModel:
        if settings.anthropic is None:
            raise ValueError(
                "Anthropic model selected but ANTHROPIC__API_KEY is not set. "
                "Add ANTHROPIC__API_KEY to your environment or .env file."
            )
        return AnthropicModel(
            self.model_name,
            provider=AnthropicProvider(
                api_key=settings.anthropic.api_key,
                http_client=create_rate_limit_client(),
            ),
        )

    def to_model(self) -> AdmittedModel:
        return AdmittedModel(
            self._provider_model(),
            process_model_gate(self.model_name, self.max_concurrent_agents),
        )


class OpenAIAIModelConfig(BaseAIModelConfig[Literal[Provider.OPENAI]]):
    """OpenAI model config with compaction, caching, and privacy settings.

    Set `reasoning_effort` for reasoning models (e.g. o-series, GPT-5.x) to trade cost for
    quality (`"low"` / `"medium"` / `"high"`). When `None` the model's default is used.

    Set `reasoning_summary` so the API returns reasoning summaries (e.g. for Logfire / debugging).
    Default `"auto"` picks the highest available reasoning-summary level for the model; set to `None` to omit
    `openai_reasoning_summary` (summaries are opt-in). See the comment on `reasoning_summary` below.

    ``openai_previous_response_id="auto"`` is intentionally omitted: with
    ``openai_store=False``, OpenAI does not retain responses for server-side chaining, so
    continuing with a stored ``provider_response_id`` yields ``previous_response_not_found``
    (400). Conversation context is carried in the full message history instead.
    """

    provider: Literal[Provider.OPENAI] = Provider.OPENAI
    reasoning_effort: Literal["low", "medium", "high"] | None = _OPENAI_REASONING_EFFORT
    reasoning_mode: Literal["standard", "pro"] = "standard"
    # "auto" sets the reasoning summary to the highest available level for the model (often
    # equivalent to "detailed" today; OpenAI may add finer tiers later). See:
    # https://developers.openai.com/api/docs/guides/reasoning#reasoning-summaries
    reasoning_summary: Literal["detailed", "concise", "auto"] | None = "auto"

    @property
    def model_settings(self) -> OpenAIResponsesModelSettings:
        settings = OpenAIResponsesModelSettings(
            max_tokens=self.max_tokens,
            openai_service_tier="flex",
            parallel_tool_calls=True,
            openai_prompt_cache_retention="24h",
            openai_store=False,
        )
        settings["extra_body"] = {
            "context_management": [
                {
                    "type": "compaction",
                    "compact_threshold": _OPENAI_COMPACTION_THRESHOLD_TOKENS,
                }
            ]
        }
        if self.reasoning_effort is not None:
            settings["openai_reasoning_effort"] = self.reasoning_effort
        settings["openai_reasoning_mode"] = self.reasoning_mode
        if self.reasoning_summary is not None:
            settings["openai_reasoning_summary"] = self.reasoning_summary
        return settings

    def _reasoning_mode_profile(self) -> OpenAIModelProfile | None:
        """Let Responses send ``reasoning.mode`` when it is not the API default.

        pydantic-ai 2.27 only marks ``gpt-5.6*`` as supporting that field, so
        ``gpt-6.1-sol``'s ``pro`` mode would otherwise be dropped.
        """
        if self.reasoning_mode == "standard":
            return None
        profile: OpenAIModelProfile = {"openai_responses_supports_reasoning_mode": True}
        return profile

    def _provider_model(self) -> OpenAIResponsesModel:
        if settings.openai is None:
            raise ValueError(
                "OpenAI model selected but OPENAI__API_KEY is not set. "
                "Add OPENAI__API_KEY to your environment or .env file."
            )
        return OpenAIResponsesModel(
            self.model_name,
            provider=OpenAIProvider(
                api_key=settings.openai.api_key,
                http_client=create_rate_limit_client(timeout=_LONG_RUN_TIMEOUT_SECONDS),
            ),
            profile=self._reasoning_mode_profile(),
        )

    def to_model(self) -> AdmittedModel:
        return AdmittedModel(
            self._provider_model(),
            process_model_gate(self.model_name, self.max_concurrent_agents),
        )


class GoogleAIModelConfig(BaseAIModelConfig[Literal[Provider.GOOGLE]]):
    """Google model config with explicit thinking budget.

    Set `thinking_budget_tokens` to cap Gemini 3's reasoning cost. Without a budget the model
    uses its default thinking behaviour, which has no cost-saving guarantee (unlike Anthropic's
    explicit cache, Gemini's *implicit* caching does not guarantee savings — use
    `google_cached_content` at call time via model_settings for a guaranteed discount).
    """

    provider: Literal[Provider.GOOGLE] = Provider.GOOGLE
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

    def _provider_model(self) -> GoogleModel:
        if settings.google is None:
            raise ValueError(
                "Google model selected but GOOGLE__API_KEY is not set. "
                "Add GOOGLE__API_KEY to your environment or .env file."
            )
        return GoogleModel(
            self.model_name,
            provider=GoogleProvider(
                api_key=settings.google.api_key,
                http_client=create_rate_limit_client(),
            ),
        )

    def to_model(self) -> AdmittedModel:
        return AdmittedModel(
            self._provider_model(),
            process_model_gate(self.model_name, self.max_concurrent_agents),
        )


class DeepSeekAIModelConfig(BaseAIModelConfig[Literal[Provider.DEEPSEEK]]):
    """DeepSeek model config using the OpenAI-compatible Chat Completions API.

    DeepSeek V4 supports thinking mode through the OpenAI-compatible
    ``reasoning_effort`` parameter plus a provider-specific ``thinking`` body field.
    Pydantic AI's ``DeepSeekProvider`` maps the returned ``reasoning_content`` field
    into thinking parts and handles sending thinking parts back during tool use.
    """

    provider: Literal[Provider.DEEPSEEK] = Provider.DEEPSEEK
    reasoning_effort: Literal["low", "medium", "high", "xhigh"] | None = (
        _DEEPSEEK_REASONING_EFFORT
    )

    @property
    def model_settings(self) -> OpenAIChatModelSettings:
        settings = OpenAIChatModelSettings(
            max_tokens=self.max_tokens,
            parallel_tool_calls=True,
            extra_body={"thinking": {"type": "enabled"}},
        )
        if self.reasoning_effort is not None:
            settings["openai_reasoning_effort"] = self.reasoning_effort
        return settings

    def _provider_model(self) -> OpenAIChatModel:
        if settings.deepseek is None:
            raise ValueError(
                "DeepSeek model selected but DEEPSEEK__API_KEY is not set. "
                "Add DEEPSEEK__API_KEY to your environment or .env file."
            )
        return OpenAIChatModel(
            self.model_name,
            provider=DeepSeekProvider(
                api_key=settings.deepseek.api_key,
                http_client=create_rate_limit_client(timeout=_LONG_RUN_TIMEOUT_SECONDS),
            ),
        )

    def to_model(self) -> AdmittedModel:
        return AdmittedModel(
            self._provider_model(),
            process_model_gate(self.model_name, self.max_concurrent_agents),
        )


AIModelConfig = Annotated[
    AnthropicAIModelConfig
    | OpenAIAIModelConfig
    | GoogleAIModelConfig
    | DeepSeekAIModelConfig,
    Field(discriminator="provider"),
]


class AIModelsConfig(BaseModel):
    model_name: ModelName
    cache_messages: bool = True

    @computed_field
    @property
    def pydantic_ai_model(self) -> AIModelConfig:
        match self.model_name:
            case ModelName.CLAUDE_OPUS_4_6 | ModelName.CLAUDE_SONNET_4_6:
                return AnthropicAIModelConfig(
                    model_name=self.model_name,
                    max_tokens=_MAX_TOKENS,
                    usage_limits=_USAGE_LIMITS,
                    cache_messages=self.cache_messages,
                )
            case (
                ModelName.CLAUDE_OPUS_4_5
                | ModelName.CLAUDE_SONNET_4_5
                | ModelName.CLAUDE_HAIKU_4_6
            ):
                return AnthropicAIModelConfig(
                    model_name=self.model_name,
                    max_tokens=_MAX_TOKENS,
                    thinking_budget_tokens=_MAX_THINKING_BUDGET_TOKENS,
                    usage_limits=_USAGE_LIMITS,
                    cache_messages=self.cache_messages,
                    effort=None,
                )
            case ModelName.GPT_6_1_SOL:
                return OpenAIAIModelConfig(
                    model_name=self.model_name,
                    max_tokens=_MAX_TOKENS,
                    usage_limits=_USAGE_LIMITS,
                    max_concurrent_agents=5,
                    reasoning_mode="pro",
                )
            case ModelName.GPT_6_LUNA:
                return OpenAIAIModelConfig(
                    model_name=self.model_name,
                    max_tokens=_MAX_TOKENS,
                    usage_limits=_USAGE_LIMITS,
                    max_concurrent_agents=20,
                )
            case (
                ModelName.GPT_5_1
                | ModelName.GPT_5_2
                | ModelName.GPT_5_4
                | ModelName.GPT_5_6_LUNA
                | ModelName.GPT_5_6_TERRA
            ):
                return OpenAIAIModelConfig(
                    model_name=self.model_name,
                    max_tokens=_MAX_TOKENS,
                    usage_limits=_USAGE_LIMITS,
                )
            case ModelName.GEMINI_3_PRO_PREVIEW | ModelName.GEMINI_3_1_PRO_PREVIEW:
                return GoogleAIModelConfig(
                    model_name=self.model_name,
                    max_tokens=_MAX_TOKENS,
                    thinking_budget_tokens=_MAX_THINKING_BUDGET_TOKENS,
                    usage_limits=_USAGE_LIMITS,
                )
            case ModelName.DEEPSEEK_V4_FLASH | ModelName.DEEPSEEK_V4_PRO:
                return DeepSeekAIModelConfig(
                    model_name=self.model_name,
                    max_tokens=_MAX_TOKENS,
                    usage_limits=_USAGE_LIMITS,
                )
            case _:
                assert_never(self.model_name)
