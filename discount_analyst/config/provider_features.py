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
    # Providers that need a text-only local web_fetch workaround (not native support).
    # Unlike MCP, membership means the provider rejects binary tool results and needs
    # markitdown conversion instead of the default WebFetch local implementation.
    TEXT_ONLY_WEB_FETCH = "text_only_web_fetch"


PROVIDERS_BY_FEATURE: Final[dict[ProviderFeature, tuple[Provider, ...]]] = {
    ProviderFeature.MCP: (Provider.ANTHROPIC, Provider.OPENAI, Provider.DEEPSEEK),
    ProviderFeature.TEXT_ONLY_WEB_FETCH: (Provider.DEEPSEEK,),
}
