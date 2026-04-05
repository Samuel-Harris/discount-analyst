from pydantic_ai import Agent

from discount_analyst.agents.common.agent_factory import AgentSpec, create_agent
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.agents.profiler.schema import ProfilerOutput
from discount_analyst.agents.profiler.system_prompt import SYSTEM_PROMPT
from discount_analyst.config.ai_models_config import AIModelsConfig

PROFILER_AGENT_SPEC = AgentSpec(
    name=AgentName.PROFILER,
    output_type=ProfilerOutput,
    system_prompt=SYSTEM_PROMPT,
)


def create_profiler_agent(
    *,
    ai_models_config: AIModelsConfig,
    use_perplexity: bool = False,
    use_mcp_financial_data: bool = True,
) -> Agent[None, ProfilerOutput]:
    """Create and configure the Profiler agent for single-ticker deep profiling."""
    return create_agent(
        spec=PROFILER_AGENT_SPEC,
        ai_models_config=ai_models_config,
        enable_web_research_tools=True,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
    )
