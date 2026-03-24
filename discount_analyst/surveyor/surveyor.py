from pydantic_ai import AbstractToolset, Agent, WebFetchTool, WebSearchTool
from pydantic_ai.builtin_tools import AbstractBuiltinTool

from discount_analyst.shared.ai.history_processors import (
    get_history_processors_for_model,
)
from discount_analyst.shared.ai.model import create_model_from_config
from discount_analyst.shared.config.ai_models_config import AIModelsConfig
from discount_analyst.shared.constants.agents import AgentName
from discount_analyst.shared.constants.providers import ProviderFeature
from discount_analyst.shared.models.data_types import SurveyorOutput
from discount_analyst.shared.tools.perplexity import create_perplexity_toolset
from discount_analyst.surveyor.system_prompt import SYSTEM_PROMPT


def create_surveyor_agent(
    ai_models_config: AIModelsConfig,
    /,
    *,
    use_perplexity: bool = True,
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

    agent = Agent(
        model=create_model_from_config(ai_models_config.model),
        output_type=SurveyorOutput,
        model_settings=ai_models_config.model.model_settings,
        system_prompt=SYSTEM_PROMPT,
        history_processors=get_history_processors_for_model(
            ai_models_config.model_name
        ),
        builtin_tools=builtin_tools,
        toolsets=toolsets,
    )

    return agent
