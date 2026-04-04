from pydantic_ai import Agent

from discount_analyst.agents.surveyor.system_prompt import SYSTEM_PROMPT
from discount_analyst.shared.ai.agent_factory import (
    AgentSpec,
    create_agent,
)
from discount_analyst.shared.config.ai_models_config import AIModelsConfig
from discount_analyst.shared.constants.agents import AgentName
from discount_analyst.shared.schemas.surveyor import SurveyorOutput

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
) -> Agent[None, SurveyorOutput]:
    """Create and configure the surveyor agent.

    Args:
        ai_models_config: Model and caching configuration.
        use_perplexity: When True, registers Perplexity-backed
            ``web_search`` and ``sec_filings_search`` tools. When False (default),
            those tools are omitted and pydantic-ai's built-in
            ``WebSearchTool`` is used instead (model-native web search).
            When Perplexity is disabled, ``WebFetchTool`` is also added for
            Anthropic and Gemini so the agent can fetch content from URLs.
        use_mcp_financial_data: When True (default), registers EODHD and FMP
            MCP toolsets for providers that support MCP (Anthropic, OpenAI).
            Use False or ``--no-mcp`` for Google or when MCP should be omitted.

    Returns:
        A configured Agent instance for discovering cheap small-cap stock candidates.
    """
    return create_agent(
        spec=SURVEYOR_AGENT_SPEC,
        ai_models_config=ai_models_config,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
    )
