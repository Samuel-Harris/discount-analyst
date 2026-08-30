from pydantic_ai import Agent

from discount_analyst.agents.curator.schema import CuratorProposal
from discount_analyst.agents.curator.system_prompt import SYSTEM_PROMPT
from discount_analyst.agents.runtime.agent_factory import AgentSpec, create_agent
from discount_analyst.agents.runtime.agent_names import AgentName
from discount_analyst.agents.runtime.terminal_run import terminal_run_options
from discount_analyst.config.ai_models_config import AIModelsConfig
from discount_analyst.config.settings import settings as app_settings

CURATOR_AGENT_SPEC = AgentSpec(
    name=AgentName.CURATOR,
    output_type=CuratorProposal,
    system_prompt=SYSTEM_PROMPT,
)


def create_curator_agent(
    ai_models_config: AIModelsConfig,
) -> Agent[None, CuratorProposal]:
    """Create the closed-book workflow-level Curator agent.

    Curator does not register web search, Perplexity, MCP financial data,
    official filings, or a live terminal session. Dashboard research flags are
    not forwarded. Frankfurter remains attached by the shared factory but must
    not be called.
    """
    return create_agent(
        spec=CURATOR_AGENT_SPEC,
        ai_models_config=ai_models_config,
        enable_web_research_tools=False,
        use_perplexity=False,
        use_mcp_financial_data=False,
        terminal=terminal_run_options(app_settings, enabled=False),
    )
