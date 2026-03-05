from pydantic_ai import AbstractToolset, Agent, WebFetchTool, WebSearchTool
from pydantic_ai.builtin_tools import AbstractBuiltinTool

from discount_analyst.shared.ai.model import create_model_from_config
from discount_analyst.shared.config.ai_models_config import AIModelsConfig
from discount_analyst.shared.constants.agents import AgentName
from discount_analyst.shared.constants.providers import ProviderFeature
from discount_analyst.shared.utils.agent_tools import (
    add_required_feature_to_builtin_tools,
)
from discount_analyst.surveyor.data_types import SurveyorOutput
from discount_analyst.shared.tools.perplexity import create_perplexity_toolset
from discount_analyst.surveyor.system_prompt import SYSTEM_PROMPT


def create_surveyor_agent(
    ai_models_config: AIModelsConfig,
    /,
    *,
    use_perplexity: bool = True,
    use_mcp_financial_data: bool = True,
) -> Agent[None, SurveyorOutput]:
    """Create and configure the surveyor agent.

    Args:
        ai_models_config: Model and caching configuration.
        use_perplexity: When True (default), registers Perplexity-backed
            ``web_search`` and ``sec_filings_search`` tools. When False,
            those tools are omitted and pydantic-ai's built-in
            ``WebSearchTool`` is used instead (model-native web search).
            When Perplexity is disabled, ``WebFetchTool`` is also added for
            Anthropic and Gemini so the agent can fetch content from URLs.
        use_mcp_financial_data: When True (default), adds EODHD and FMP
            MCPServerStreamableHTTP toolsets for financial data. pydantic-ai
            manages the MCP connection and exposes tools natively, avoiding
            the list_tools conversation overhead of the old MCPServerTool
            builtin. Raises NotImplementedError if the provider does not
            support the MCP feature.

    Returns:
        A configured Agent instance for discovering cheap small-cap stock candidates.
    """
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
        toolsets.append(create_perplexity_toolset(AgentName.SURVEYOR))

    if use_mcp_financial_data:
        add_required_feature_to_builtin_tools(
            required_feature=ProviderFeature.MCP,
            toolsets=toolsets,
            provider=ai_models_config.model.provider,
        )

    agent = Agent(
        model=create_model_from_config(ai_models_config.model),
        output_type=SurveyorOutput,
        model_settings=ai_models_config.model.model_settings,
        system_prompt=SYSTEM_PROMPT,
        builtin_tools=builtin_tools,
        toolsets=toolsets,
    )

    return agent
