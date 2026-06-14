"""Provider and feature constants for AI model capabilities."""

from enum import StrEnum
from typing import Final


class Provider(StrEnum):
    """AI model providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"


class ProviderFeature(StrEnum):
    """Features that may or may not be supported by each provider."""

    MCP = "mcp"
    TEXT_ONLY_WEB_FETCH = "text_only_web_fetch"


PROVIDERS_BY_FEATURE: Final[dict[ProviderFeature, tuple[Provider, ...]]] = {
    ProviderFeature.MCP: (Provider.ANTHROPIC, Provider.OPENAI, Provider.DEEPSEEK),
    ProviderFeature.TEXT_ONLY_WEB_FETCH: (Provider.DEEPSEEK,),
}
