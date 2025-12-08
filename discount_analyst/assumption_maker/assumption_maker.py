from aiolimiter import AsyncLimiter
from perplexity import AsyncPerplexity
from pydantic_ai import Agent
import logfire
from discount_analyst.shared.data_types import StockAssumptions
from discount_analyst.shared import AIModelsConfig, settings
from discount_analyst.assumption_maker.system_prompt import SYSTEM_PROMPT

perplexity_rate_limiter = AsyncLimiter(settings.perplexity.rate_limit_per_minute, 60)


def create_assumption_maker_agent() -> Agent[StockAssumptions]:
    """Create and configure the assumption maker agent.

    Returns:
        A configured Agent instance for making stock assumptions.
    """

    logfire.configure(token=settings.pydantic.logfire_api_key)
    logfire.instrument_pydantic_ai()

    ai_models_config = AIModelsConfig()

    agent = Agent(
        model=ai_models_config.assumption_maker.model,
        output_type=StockAssumptions,
        model_settings=ai_models_config.assumption_maker.model_settings,
        system_prompt=SYSTEM_PROMPT,
    )

    @agent.tool_plain(docstring_format="google", require_parameter_descriptions=True)
    async def web_search(question: str) -> str:
        """Search the web for financial data, company information, or market analysis. Ask a question, and another LLM will prove the answer using information from the web.

        Use this tool to find:
        - Historical financial statements (10-K, 10-Q filings)
        - Industry peer comparisons and benchmarks
        - Analyst estimates and projections
        - Tax rates and regulatory information
        - Economic forecasts (GDP growth, inflation)
        - Company news and recent developments

        Args:
            question: The question to ask. This should be in natural language.

        Returns:
            The answer to the question.
        """

        async with perplexity_rate_limiter:
            client = AsyncPerplexity(api_key=settings.perplexity.api_key)
            completion = await client.chat.completions.create(
                messages=[{"role": "user", "content": question}],
                model="sonar",
            )
            return completion.choices[0].message.content

    return agent
