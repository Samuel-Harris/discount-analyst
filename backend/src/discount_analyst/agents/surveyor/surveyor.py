from pydantic_ai import Agent

from discount_analyst.agents.surveyor.system_prompt import SYSTEM_PROMPT
from discount_analyst.agents.runtime.agent_factory import (
    AgentSpec,
    create_agent,
)
from discount_analyst.agents.runtime.agent_names import AgentName
from discount_analyst.agents.runtime.terminal_run import TerminalRunOptions
from discount_analyst.agents.surveyor.schema import SurveyorOutput
from discount_analyst.config.ai_models_config import AIModelsConfig

SURVEYOR_AGENT_SPEC = AgentSpec(
    name=AgentName.SURVEYOR,
    output_type=SurveyorOutput,
    system_prompt=SYSTEM_PROMPT,
)


def create_surveyor_agent(
    *,
    ai_models_config: AIModelsConfig,
    use_perplexity: bool = False,
    use_mcp_financial_data: bool = True,
    terminal: TerminalRunOptions | None = None,
) -> Agent[None, SurveyorOutput]:
    """Create and configure the surveyor agent.

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
        A configured Agent instance for discovering cheap small-cap stock candidates.
    """
    return create_agent(
        spec=SURVEYOR_AGENT_SPEC,
        ai_models_config=ai_models_config,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
        terminal=terminal,
    )
