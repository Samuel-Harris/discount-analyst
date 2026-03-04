"""Utilities for configuring agent tools."""

from pydantic_ai.builtin_tools import AbstractBuiltinTool

from discount_analyst.shared.constants.providers import (
    PROVIDERS_BY_FEATURE,
    Provider,
    ProviderFeature,
)
from discount_analyst.shared.mcp.financial_data import create_financial_data_mcp_tools


def add_required_feature_to_builtin_tools(
    *,
    builtin_tools: list[AbstractBuiltinTool],
    required_feature: ProviderFeature,
    provider: Provider,
) -> None:
    """Extend builtin_tools with the toolset if the provider supports the feature.

    Args:
        required_feature: The feature the provider must support (e.g. MCP).
        builtin_tools: The list to extend. Modified in place.
        provider: The model provider.
        toolset_factory: Callable that returns the tools to add. Only invoked
            when the provider supports the feature.

    Raises:
        NotImplementedError: If the provider does not support the required feature.
    """
    if provider not in PROVIDERS_BY_FEATURE[required_feature]:
        supported = ", ".join(p.value for p in PROVIDERS_BY_FEATURE[required_feature])
        raise NotImplementedError(
            f"Feature '{required_feature.value}' is not supported by provider "
            f"'{provider.value}'. Supported providers: {supported}."
        )

    match required_feature:
        case ProviderFeature.MCP:
            builtin_tools.extend(create_financial_data_mcp_tools())
        case _:
            raise NotImplementedError(
                f"Feature '{required_feature.value}' is not supported."
            )
