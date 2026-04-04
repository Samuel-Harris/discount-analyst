from pydantic_ai import Agent

from discount_analyst.agents.researcher.system_prompt import SYSTEM_PROMPT
from discount_analyst.shared.ai import agent_factory
from discount_analyst.shared.config.ai_models_config import AIModelsConfig
from discount_analyst.shared.constants.agents import AgentName
from discount_analyst.shared.schemas.researcher import DeepResearchReport


def create_researcher_agent(
    ai_models_config: AIModelsConfig,
    /,
    *,
    use_perplexity: bool = False,
    use_mcp_financial_data: bool = True,
) -> Agent[None, DeepResearchReport]:
    """Create and configure the researcher agent.

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
        A configured Agent instance for producing deep research evidence reports.
    """
    return agent_factory.create_agent(
        ai_models_config,
        name=AgentName.RESEARCHER,
        output_type=DeepResearchReport,
        system_prompt=SYSTEM_PROMPT,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
    )
