from pydantic_ai import Agent

from discount_analyst.agents.strategist.system_prompt import SYSTEM_PROMPT
from discount_analyst.shared.ai.history_processors import (
    get_history_processors_for_model,
)
from discount_analyst.shared.ai.model import create_model_from_config
from discount_analyst.shared.config.ai_models_config import AIModelsConfig
from discount_analyst.shared.constants.agents import AgentName
from discount_analyst.shared.schemas.strategist import MispricingThesis


def create_strategist_agent(
    ai_models_config: AIModelsConfig,
) -> Agent[None, MispricingThesis]:
    """Create and configure the Strategist agent (interpretation only; no web/MCP tools).

    Args:
        ai_models_config: Model and caching configuration.

    Returns:
        A configured Agent instance for producing `MispricingThesis` output.
    """
    return Agent(
        name=AgentName.STRATEGIST,
        model=create_model_from_config(ai_models_config.model),
        output_type=MispricingThesis,
        model_settings=ai_models_config.model.model_settings,
        system_prompt=SYSTEM_PROMPT,
        history_processors=get_history_processors_for_model(
            ai_models_config.model_name
        ),
    )
