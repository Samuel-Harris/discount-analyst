from pydantic_ai import Agent

from discount_analyst.agents.arbiter.schema import ArbiterDecision
from discount_analyst.agents.arbiter.system_prompt import SYSTEM_PROMPT
from discount_analyst.agents.common.agent_factory import AgentSpec, create_agent
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.config.ai_models_config import AIModelsConfig

ARBITER_AGENT_SPEC = AgentSpec(
    name=AgentName.ARBITER,
    output_type=ArbiterDecision,
    system_prompt=SYSTEM_PROMPT,
)


def create_arbiter_agent(
    ai_models_config: AIModelsConfig,
) -> Agent[None, ArbiterDecision]:
    """Create the Arbiter agent (interpretation only — no web search or MCP tools)."""
    return create_agent(
        spec=ARBITER_AGENT_SPEC,
        ai_models_config=ai_models_config,
        enable_web_research_tools=False,
        use_mcp_financial_data=False,
    )
