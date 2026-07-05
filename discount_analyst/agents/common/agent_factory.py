"""Shared factory for pipeline agents that use web search, fetch, and financial MCP."""

from dataclasses import dataclass
from typing import Any

from pydantic_ai import AbstractToolset, Agent, Tool, ToolOutput
from pydantic_ai.capabilities import AgentCapability, WebFetch

from common.config import settings as app_settings
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.agents.common_prompts.current_date import with_current_date
from discount_analyst.agents.common.model import create_model_from_config
from discount_analyst.agents.common.terminal_run import (
    TerminalRunOptions,
    terminal_run_options,
)
from discount_analyst.agents.common.tool_support import (
    add_required_feature_to_builtin_tools,
)
from discount_analyst.config.ai_models_config import AIModelsConfig
from discount_analyst.config.provider_features import (
    PROVIDERS_BY_FEATURE,
    Provider,
    ProviderFeature,
)
from discount_analyst.integrations.perplexity import create_perplexity_toolset
from discount_analyst.integrations.bounded_web_search import BoundedWebSearch
from discount_analyst.integrations.text_only_web_fetch import (
    create_text_only_web_fetch_tool,
)
from discount_analyst.integrations.terminal import (
    Terminal,
    TerminalLimits,
    TerminalSessionState,
)


@dataclass(frozen=True, slots=True)
class AgentSpec[OutT]:
    """Declarative config for an agent (name, schema, system prompt)."""

    name: AgentName
    output_type: type[OutT]
    system_prompt: str


@dataclass(frozen=True, slots=True)
class AgentTooling:
    """Capabilities and toolsets that will be registered on an agent."""

    capabilities: tuple[AgentCapability[None], ...] = ()
    toolsets: tuple[AbstractToolset[None], ...] = ()


def create_web_research_tooling(
    *, agent_name: AgentName, use_perplexity: bool, provider: Provider
) -> AgentTooling:
    """Build web-research tooling without leaking Pydantic AI agent internals."""
    if use_perplexity:
        return AgentTooling(toolsets=(create_perplexity_toolset(agent_name),))

    web_fetch_local: bool | Tool[Any] = True
    if provider in PROVIDERS_BY_FEATURE[ProviderFeature.TEXT_ONLY_WEB_FETCH]:
        web_fetch_local = create_text_only_web_fetch_tool()

    return AgentTooling(
        capabilities=(
            BoundedWebSearch(native=True, local="duckduckgo"),
            WebFetch(native=True, local=web_fetch_local),
        )
    )


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

    By default, the factory enables Pydantic AI's native-or-local web search
    and fetch capabilities, optional Perplexity search, and optional financial
    MCP toolsets.
    Set ``enable_web_research_tools=False`` for interpretation-only agents
    (for example, Strategist and Sentinel). When ``terminal`` is omitted, terminal
    follows ``settings.use_terminal`` only (independent of web/MCP flags).

    Structured output is always registered via ``ToolOutput`` (tool mode, ``final_result``)
    for cross-provider uniformity.
    """
    capabilities: list[AgentCapability[None]] = []
    toolsets: list[AbstractToolset[None]] = []

    terminal_opts = (
        terminal if terminal is not None else terminal_run_options(app_settings)
    )
    if terminal_opts.enabled:
        session_state = terminal_opts.session_state or TerminalSessionState()
        capabilities.append(
            Terminal(
                service_url=terminal_opts.runtime.service_url,
                limits=TerminalLimits(
                    command_timeout_s=terminal_opts.runtime.command_timeout_s,
                    max_output_bytes=terminal_opts.runtime.max_output_bytes,
                ),
                session_id=terminal_opts.require_session_id(),
                session_state=session_state,
            )
        )

    if enable_web_research_tools:
        web_tooling = create_web_research_tooling(
            agent_name=spec.name,
            use_perplexity=use_perplexity,
            provider=ai_models_config.model.provider,
        )
        capabilities.extend(web_tooling.capabilities)
        toolsets.extend(web_tooling.toolsets)

    if use_mcp_financial_data:
        add_required_feature_to_builtin_tools(
            required_feature=ProviderFeature.MCP,
            toolsets=toolsets,
            provider=ai_models_config.model.provider,
        )

    return Agent(
        name=spec.name,
        output_type=ToolOutput(spec.output_type),
        model=create_model_from_config(ai_models_config.model),
        model_settings=ai_models_config.model.model_settings,
        system_prompt=with_current_date(spec.system_prompt),
        capabilities=capabilities,
        toolsets=toolsets,
    )
