from pydantic_ai import Agent

from discount_analyst.agents.researcher.system_prompt import SYSTEM_PROMPT
from discount_analyst.agents.common.agent_factory import (
    AgentSpec,
    create_agent,
)
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.agents.common.terminal_run import TerminalRunOptions
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.config.ai_models_config import AIModelsConfig

RESEARCHER_AGENT_SPEC = AgentSpec(
    name=AgentName.RESEARCHER,
    output_type=DeepResearchReport,
    system_prompt=SYSTEM_PROMPT,
)


def create_researcher_agent(
    ai_models_config: AIModelsConfig,
    /,
    *,
    use_perplexity: bool = False,
    use_mcp_financial_data: bool = True,
    terminal: TerminalRunOptions | None = None,
) -> Agent[None, DeepResearchReport]:
    """Create and configure the researcher agent.

    Args:
        ai_models_config: Model and caching configuration.
        use_perplexity: When True, registers Perplexity-backed
            ``web_search`` and ``sec_filings_search`` tools. When False (default),
            uses pydantic-ai's ``WebSearch`` and ``WebFetch`` capabilities,
            which use provider-native tools where supported and Pydantic AI
            local fallbacks otherwise.
        use_mcp_financial_data: When True (default), registers EODHD and FMP
            MCP toolsets for providers that support MCP (Anthropic, OpenAI,
            DeepSeek).
            Use False or ``--no-mcp`` for Google or when MCP should be omitted.
        terminal: Per-run terminal sandbox options; defaults from process settings.

    Returns:
        A configured Agent instance for producing deep research evidence reports.
    """
    return create_agent(
        spec=RESEARCHER_AGENT_SPEC,
        ai_models_config=ai_models_config,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
        terminal=terminal,
    )
