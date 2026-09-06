from pydantic_ai import Agent

from discount_analyst.agents.curator.schema import CuratorProposal
from discount_analyst.agents.curator.system_prompt import SYSTEM_PROMPT
from discount_analyst.agents.runtime.agent_factory import AgentSpec, create_agent
from discount_analyst.agents.runtime.agent_names import AgentName
from discount_analyst.agents.runtime.terminal_run import TerminalRunOptions
from discount_analyst.config.ai_models_config import AIModelsConfig

CURATOR_AGENT_SPEC = AgentSpec(
    name=AgentName.CURATOR,
    output_type=CuratorProposal,
    system_prompt=SYSTEM_PROMPT,
)


def create_curator_agent(
    ai_models_config: AIModelsConfig,
    *,
    terminal: TerminalRunOptions | None = None,
) -> Agent[None, CuratorProposal]:
    """Create the workflow-level Curator agent.

    Curator registers web search/fetch and an optional live terminal session.
    It does not register Perplexity, MCP financial data, or official filings.
    Dashboard Perplexity/MCP flags are not forwarded. Frankfurter remains
    attached by the shared factory but must not be called.
    """
    return create_agent(
        spec=CURATOR_AGENT_SPEC,
        ai_models_config=ai_models_config,
        use_perplexity=False,
        use_mcp_financial_data=False,
        terminal=terminal,
    )
