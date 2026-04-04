"""Shared factory for pipeline agents that use web search, fetch, and financial MCP."""

from dataclasses import dataclass

from pydantic_ai import AbstractToolset, Agent, WebFetchTool, WebSearchTool
from pydantic_ai.builtin_tools import AbstractBuiltinTool

from discount_analyst.shared.ai.model import create_model_from_config
from discount_analyst.shared.config.ai_models_config import AIModelsConfig
from discount_analyst.shared.constants.agents import AgentName
from discount_analyst.shared.constants.providers import ProviderFeature
from discount_analyst.shared.tools.perplexity import create_perplexity_toolset
from discount_analyst.shared.utils.agent_tools import (
    add_required_feature_to_builtin_tools,
)


@dataclass(frozen=True, slots=True)
class AgentSpec[OutT]:
    """Declarative config for an agent (name, schema, system prompt)."""

    name: AgentName
    output_type: type[OutT]
    system_prompt: str


def create_agent[OutT](
    *,
    spec: AgentSpec[OutT],
    ai_models_config: AIModelsConfig,
    use_perplexity: bool = False,
    use_mcp_financial_data: bool = True,
) -> Agent[None, OutT]:
    """Build a pydantic-ai agent from a spec with web / Perplexity / financial MCP tooling."""
    builtin_tools: list[AbstractBuiltinTool] = []
    toolsets: list[AbstractToolset[None]] = []

    if not use_perplexity:
        builtin_tools.append(WebSearchTool())

        supports_web_fetch = ai_models_config.model.supports_feature(
            ProviderFeature.WEB_FETCH
        )
        if supports_web_fetch:
            builtin_tools.append(WebFetchTool())
    else:
        toolsets.append(create_perplexity_toolset(spec.name))

    if use_mcp_financial_data:
        add_required_feature_to_builtin_tools(
            required_feature=ProviderFeature.MCP,
            toolsets=toolsets,
            provider=ai_models_config.model.provider,
        )

    return Agent(
        name=spec.name,
        model=create_model_from_config(ai_models_config.model),
        output_type=spec.output_type,
        model_settings=ai_models_config.model.model_settings,
        system_prompt=spec.system_prompt,
        builtin_tools=builtin_tools,
        toolsets=toolsets,
    )
