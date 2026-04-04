from pydantic_ai import AbstractToolset, Agent, WebFetchTool, WebSearchTool
from pydantic_ai.builtin_tools import AbstractBuiltinTool

from discount_analyst.shared.ai.history_processors import (
    get_history_processors_for_model,
)
from discount_analyst.shared.ai.model import create_model_from_config
from discount_analyst.shared.config.ai_models_config import AIModelsConfig
from discount_analyst.shared.constants.agents import AgentName
from discount_analyst.shared.schemas.appraiser import AppraiserOutput
from discount_analyst.shared.constants.providers import ProviderFeature
from discount_analyst.shared.utils.agent_tools import (
    add_required_feature_to_builtin_tools,
)
from discount_analyst.shared.tools.perplexity import create_perplexity_toolset
from discount_analyst.agents.appraiser.system_prompt import SYSTEM_PROMPT


def create_appraiser_agent(
    ai_models_config: AIModelsConfig,
    /,
    *,
    use_perplexity: bool = False,
    use_mcp_financial_data: bool = True,
) -> Agent[None, AppraiserOutput]:
    """Create and configure the appraiser agent.

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
        A configured Agent instance for making stock assumptions.
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
        toolsets.append(create_perplexity_toolset(AgentName.APPRAISER))

    if use_mcp_financial_data:
        add_required_feature_to_builtin_tools(
            required_feature=ProviderFeature.MCP,
            toolsets=toolsets,
            provider=ai_models_config.model.provider,
        )

    agent = Agent(
        name=AgentName.APPRAISER,
        model=create_model_from_config(ai_models_config.model),
        output_type=AppraiserOutput,
        model_settings=ai_models_config.model.model_settings,
        system_prompt=SYSTEM_PROMPT,
        history_processors=get_history_processors_for_model(
            ai_models_config.model_name
        ),
        builtin_tools=builtin_tools,
        toolsets=toolsets,
    )

    return agent
