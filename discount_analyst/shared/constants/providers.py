"""Provider and feature constants for AI model capabilities."""

from enum import StrEnum
from typing import Final


class Provider(StrEnum):
    """AI model providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


class ProviderFeature(StrEnum):
    """Features that may or may not be supported by each provider."""

    WEB_FETCH = "web_fetch"


PROVIDERS_BY_FEATURE: Final[dict[ProviderFeature, tuple[Provider, ...]]] = {
    ProviderFeature.WEB_FETCH: (Provider.ANTHROPIC, Provider.GOOGLE),
}
