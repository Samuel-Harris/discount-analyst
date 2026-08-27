from pydantic_ai import Agent

from discount_analyst.agents.runtime.agent_factory import AgentSpec, create_agent
from discount_analyst.agents.runtime.agent_names import AgentName
from discount_analyst.agents.runtime.terminal_run import terminal_run_options
from discount_analyst.agents.sentinel.schema import EvaluationReport
from discount_analyst.agents.sentinel.system_prompt import SYSTEM_PROMPT
from discount_analyst.config.ai_models_config import AIModelsConfig
from discount_analyst.config.settings import settings as app_settings

SENTINEL_AGENT_SPEC = AgentSpec(
    name=AgentName.SENTINEL,
    output_type=EvaluationReport,
    system_prompt=SYSTEM_PROMPT,
)


def create_sentinel_agent(
    ai_models_config: AIModelsConfig,
) -> Agent[None, EvaluationReport]:
    """Create the interpretation-only Sentinel agent.

    Sentinel does not register web search, Perplexity, MCP financial data, or a
    live terminal session. Dashboard research flags are not forwarded.
    """
    return create_agent(
        spec=SENTINEL_AGENT_SPEC,
        ai_models_config=ai_models_config,
        enable_web_research_tools=False,
        use_perplexity=False,
        use_mcp_financial_data=False,
        terminal=terminal_run_options(app_settings, enabled=False),
    )
