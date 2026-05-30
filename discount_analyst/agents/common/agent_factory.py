"""Shared factory for pipeline agents that use web search, fetch, and financial MCP."""

from dataclasses import dataclass

from pydantic_ai import AbstractToolset, Agent, WebFetchTool, WebSearchTool
from pydantic_ai.capabilities import AgentCapability, NativeTool

from common.config import settings as app_settings
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.agents.common.model import create_model_from_config
from discount_analyst.agents.common.terminal_run import (
    TerminalRunOptions,
    default_terminal_for_agent,
)
from discount_analyst.agents.common.tool_support import (
    add_required_feature_to_builtin_tools,
)
from discount_analyst.config.ai_models_config import AIModelsConfig
from discount_analyst.config.provider_features import ProviderFeature
from discount_analyst.integrations.perplexity import create_perplexity_toolset
from discount_analyst.integrations.terminal import Terminal, TerminalLimits


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
    enable_web_research_tools: bool = True,
    use_perplexity: bool = False,
    use_mcp_financial_data: bool = True,
    terminal: TerminalRunOptions | None = None,
) -> Agent[None, OutT]:
    """Build a pydantic-ai agent from a spec.

    By default, the factory enables model-native web search (+ optional fetch),
    optional Perplexity search, and optional financial MCP toolsets.
    Set ``enable_web_research_tools=False`` for interpretation-only agents
    (for example, Strategist and Sentinel). When ``terminal`` is omitted, terminal
    follows ``settings.use_terminal`` only (independent of web/MCP flags).
    """
    capabilities: list[AgentCapability[None]] = []
    toolsets: list[AbstractToolset[None]] = []

    terminal_opts = default_terminal_for_agent(app_settings, terminal=terminal)
    if terminal_opts.enabled:
        capabilities.append(
            Terminal(
                service_url=terminal_opts.runtime.service_url,
                limits=TerminalLimits(
                    command_timeout_s=terminal_opts.runtime.command_timeout_s,
                    max_output_bytes=terminal_opts.runtime.max_output_bytes,
                ),
            )
        )

    if enable_web_research_tools:
        if not use_perplexity:
            capabilities.append(NativeTool(WebSearchTool()))

            supports_web_fetch = ai_models_config.model.supports_feature(
                ProviderFeature.WEB_FETCH
            )
            if supports_web_fetch:
                capabilities.append(NativeTool(WebFetchTool()))
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
        output_type=spec.output_type,
        model=create_model_from_config(ai_models_config.model),
        model_settings=ai_models_config.model.model_settings,
        system_prompt=spec.system_prompt,
        capabilities=capabilities,
        toolsets=toolsets,
    )
