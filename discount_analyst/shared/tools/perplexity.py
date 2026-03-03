"""Shared Perplexity-backed search tools for AI agents."""

from aiolimiter import AsyncLimiter
from perplexity import AsyncPerplexity
from pydantic_ai import FunctionToolset

from discount_analyst.shared.config.settings import settings
from discount_analyst.shared.constants.agents import AgentName
from discount_analyst.shared.tools.descriptions import AGENT_TOOL_DESCRIPTIONS

perplexity_rate_limiter = AsyncLimiter(settings.perplexity.rate_limit_per_minute, 60)


async def _web_search_impl(question: str) -> str:
    """Web search implementation.

    Args:
        question: The question to ask in natural language.

    Returns:
        The answer to the question based on web sources.
    """
    async with perplexity_rate_limiter:
        client = AsyncPerplexity(api_key=settings.perplexity.api_key)
        response = await client.chat.completions.create(
            messages=[{"role": "user", "content": question}],
            model="sonar",
            search_mode="web",
        )
        response_content = response.choices[0].message.content

        if isinstance(response_content, str):
            return response_content
        raise ValueError(
            f"Perplexity API returned unexpected response type from web_search. "
            f"Expected: string content. Received: {type(response_content).__name__} "
            f"with value: {response_content}. This indicates an API response format change."
        )


async def _sec_filings_search_impl(question: str) -> str:
    """SEC filings search implementation.

    Args:
        question: The question to ask in natural language.

    Returns:
        The answer to the question based on SEC filings.
    """
    async with perplexity_rate_limiter:
        client = AsyncPerplexity(api_key=settings.perplexity.api_key)
        response = await client.chat.completions.create(
            messages=[{"role": "user", "content": question}],
            model="sonar",
            search_mode="sec",
        )
        response_content = response.choices[0].message.content

        if isinstance(response_content, str):
            return response_content
        raise ValueError(
            f"Perplexity API returned unexpected response type from sec_filings_search. "
            f"Expected: string content. Received: {type(response_content).__name__} "
            f"with value: {response_content}. This indicates an API response format change."
        )


def create_perplexity_toolset(agent_name: AgentName) -> FunctionToolset[None]:
    """Create a Perplexity-backed toolset for the given agent.

    Args:
        agent_name: The agent to create the toolset for. Must be registered
            in AGENT_TOOL_DESCRIPTIONS.

    Returns:
        A FunctionToolset with web_search and sec_filings_search tools.
    """
    descriptions = AGENT_TOOL_DESCRIPTIONS[agent_name]
    toolset = FunctionToolset[None]()

    toolset.add_function(
        _web_search_impl,
        name="web_search",
        description=descriptions.web_search,
        docstring_format="google",
        require_parameter_descriptions=True,
    )
    toolset.add_function(
        _sec_filings_search_impl,
        name="sec_filings_search",
        description=descriptions.sec_filings_search,
        docstring_format="google",
        require_parameter_descriptions=True,
    )

    return toolset
