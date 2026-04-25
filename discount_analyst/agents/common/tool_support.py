"""Utilities for configuring agent tools."""

from pydantic_ai import AbstractToolset

from discount_analyst.config.provider_features import (
    PROVIDERS_BY_FEATURE,
    Provider,
    ProviderFeature,
)
from discount_analyst.integrations.financial_data_mcp import (
    create_financial_data_mcp_servers,
)
from discount_analyst.integrations.infallible_toolset import InfallibleToolset


def add_required_feature_to_builtin_tools(
    *,
    toolsets: list[AbstractToolset[None]],
    required_feature: ProviderFeature,
    provider: Provider,
) -> None:
    """Extend toolsets with the appropriate tools for the feature.

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
            # Wrap MCP servers with InfallibleToolset so tool errors (e.g., 402
            # Payment Required) are returned as error messages to the model
            # instead of crashing the agent run.
            for mcp_server in create_financial_data_mcp_servers():
                toolsets.append(InfallibleToolset(mcp_server))
        case _:
            raise NotImplementedError(
                f"Feature '{required_feature.value}' is not supported."
            )
