from pydantic_ai import AbstractToolset, Agent, WebFetchTool, WebSearchTool
from pydantic_ai.builtin_tools import AbstractBuiltinTool

from discount_analyst.shared.ai.history_processors import (
    get_history_processors_for_model,
)
from discount_analyst.shared.ai.model import create_model_from_config
from discount_analyst.shared.constants.providers import ProviderFeature
from discount_analyst.shared.config.ai_models_config import AIModelsConfig
from discount_analyst.shared.constants.agents import AgentName
from discount_analyst.appraiser.data_types import AppraiserOutput
from discount_analyst.appraiser.user_prompt import create_user_prompt
from discount_analyst.shared.models.data_types import SurveyorCandidate
from discount_analyst.shared.tools.perplexity import create_perplexity_toolset
from discount_analyst.appraiser.system_prompt import SYSTEM_PROMPT


def create_appraiser_user_prompt(
    *, research_report: str, surveyor_candidate: SurveyorCandidate
) -> str:
    """Build the user prompt for a DCF/appraiser run using research + surveyor context."""
    return create_user_prompt(
        ticker=surveyor_candidate.ticker,
        research_report=research_report,
        surveyor_candidate=surveyor_candidate,
    )


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

    agent = Agent(
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
