from pydantic_ai import Agent, WebFetchTool, WebSearchTool
from pydantic_ai.builtin_tools import AbstractBuiltinTool

from discount_analyst.shared.ai.model import create_model_from_config
from discount_analyst.shared.config.ai_models_config import AIModelsConfig
from discount_analyst.shared.constants.agents import AgentName
from discount_analyst.shared.models.data_types import AppraiserOutput
from discount_analyst.shared.tools.perplexity import create_perplexity_toolset
from discount_analyst.appraiser.system_prompt import SYSTEM_PROMPT


def create_appraiser_agent(
    ai_models_config: AIModelsConfig,
    /,
    *,
    use_perplexity: bool = True,
) -> Agent[None, AppraiserOutput]:
    """Create and configure the appraiser agent.

    Args:
        ai_models_config: Model and caching configuration.
        use_perplexity: When True (default), registers Perplexity-backed
            ``web_search`` and ``sec_filings_search`` tools. When False,
            those tools are omitted and pydantic-ai's built-in
            ``WebSearchTool`` is used instead (model-native web search).
            When Perplexity is disabled, ``WebFetchTool`` is also added for
            Anthropic and Gemini so the agent can fetch content from URLs.

    Returns:
        A configured Agent instance for making stock assumptions.
    """

    provider = ai_models_config.model.provider
    supports_web_fetch = provider in ("anthropic", "google")

    if not use_perplexity:
        builtin_tools: list[AbstractBuiltinTool] = [WebSearchTool()]

        if supports_web_fetch:
            builtin_tools.append(WebFetchTool())
    else:
        builtin_tools = []

    agent = Agent(
        model=create_model_from_config(ai_models_config.model),
        output_type=AppraiserOutput,
        model_settings=ai_models_config.model.model_settings,
        system_prompt=SYSTEM_PROMPT,
        builtin_tools=builtin_tools,
        toolsets=[create_perplexity_toolset(AgentName.APPRAISER)]
        if use_perplexity
        else [],
    )

    return agent
