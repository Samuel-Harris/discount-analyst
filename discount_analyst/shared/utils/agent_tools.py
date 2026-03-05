"""Utilities for configuring agent tools."""

from pydantic_ai import AbstractToolset

from discount_analyst.shared.constants.providers import (
    PROVIDERS_BY_FEATURE,
    Provider,
    ProviderFeature,
)
from discount_analyst.shared.mcp.financial_data import create_financial_data_mcp_servers


def add_required_feature_to_builtin_tools(
    *,
    toolsets: list[AbstractToolset],
    required_feature: ProviderFeature,
    provider: Provider,
) -> None:
    """Extend builtin_tools or toolsets with the appropriate tools for the feature.

    Args:
        required_feature: The feature the provider must support (e.g. MCP).
        toolsets: Toolsets list (modified in place where applicable).
        provider: The model provider.

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
            toolsets.extend(create_financial_data_mcp_servers())
        case _:
            raise NotImplementedError(
                f"Feature '{required_feature.value}' is not supported."
            )
