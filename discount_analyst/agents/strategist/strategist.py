from pydantic_ai import Agent

from discount_analyst.agents.strategist.system_prompt import SYSTEM_PROMPT
from discount_analyst.agents.common.agent_factory import (
    AgentSpec,
    create_agent,
)
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.config.ai_models_config import AIModelsConfig

STRATEGIST_AGENT_SPEC = AgentSpec(
    name=AgentName.STRATEGIST,
    output_type=MispricingThesis,
    system_prompt=SYSTEM_PROMPT,
)


def create_strategist_agent(
    ai_models_config: AIModelsConfig,
) -> Agent[None, MispricingThesis]:
    """Create and configure the Strategist agent (interpretation only; no web/MCP tools).

    Args:
        ai_models_config: Model and caching configuration.

    Returns:
        A configured Agent instance for producing `MispricingThesis` output.
    """
    return create_agent(
        spec=STRATEGIST_AGENT_SPEC,
        ai_models_config=ai_models_config,
        enable_web_research_tools=False,
        use_mcp_financial_data=False,
    )
