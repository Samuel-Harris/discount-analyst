from pydantic_ai import Agent

from discount_analyst.agents.runtime.agent_factory import AgentSpec, create_agent
from discount_analyst.agents.runtime.agent_names import AgentName
from discount_analyst.agents.runtime.terminal_run import TerminalRunOptions
from discount_analyst.agents.sentinel.schema import EvaluationReport
from discount_analyst.agents.sentinel.system_prompt import SYSTEM_PROMPT
from discount_analyst.config.ai_models_config import AIModelsConfig

SENTINEL_AGENT_SPEC = AgentSpec(
    name=AgentName.SENTINEL,
    output_type=EvaluationReport,
    system_prompt=SYSTEM_PROMPT,
)


def create_sentinel_agent(
    ai_models_config: AIModelsConfig,
    *,
    terminal: TerminalRunOptions | None = None,
) -> Agent[None, EvaluationReport]:
    """Create and configure the Sentinel agent (no web/MCP tools).

    Args:
        ai_models_config: Model and caching configuration.
        terminal: Per-run terminal options; omitted terminal is off unless passed explicitly.

    Returns:
        A configured Agent instance for producing `EvaluationReport` output.
    """
    return create_agent(
        spec=SENTINEL_AGENT_SPEC,
        ai_models_config=ai_models_config,
        enable_web_research_tools=False,
        use_mcp_financial_data=False,
        terminal=terminal,
    )
