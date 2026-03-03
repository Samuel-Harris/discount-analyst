from aiolimiter import AsyncLimiter
from perplexity import AsyncPerplexity
from pydantic_ai import Agent, WebFetchTool, WebSearchTool
from pydantic_ai.builtin_tools import AbstractBuiltinTool
from discount_analyst.shared.ai.model import create_model_from_config
from discount_analyst.shared.config.ai_models_config import AIModelsConfig
from discount_analyst.shared.config.settings import settings
from discount_analyst.shared.models.data_types import AppraiserOutput
from discount_analyst.appraiser.system_prompt import SYSTEM_PROMPT

perplexity_rate_limiter = AsyncLimiter(settings.perplexity.rate_limit_per_minute, 60)


def create_appraiser_agent(
    ai_models_config: AIModelsConfig,
    /,
    *,
    use_perplexity: bool = True,
) -> Agent[None, AppraiserOutput]:
    """Create and configure the appraiser agent.

    Args:
        ai_models_config: Model and caching configuration.
        use_perplexity: When True (default), registers Perplexity-backed
            ``web_search`` and ``sec_filings_search`` tools. When False,
            those tools are omitted and pydantic-ai's built-in
            ``WebSearchTool`` is used instead (model-native web search).
            When Perplexity is disabled, ``WebFetchTool`` is also added for
            Anthropic and Gemini so the agent can fetch content from URLs.

    Returns:
        A configured Agent instance for making stock assumptions.
    """

    provider = ai_models_config.model.provider
    supports_web_fetch = provider in ("anthropic", "google")

    if not use_perplexity:
        builtin_tools: list[AbstractBuiltinTool] = [WebSearchTool()]

        if supports_web_fetch:
            builtin_tools.append(WebFetchTool())
    else:
        builtin_tools = []

    agent = Agent(
        model=create_model_from_config(ai_models_config.model),
        output_type=AppraiserOutput,
        model_settings=ai_models_config.model.model_settings,
        system_prompt=SYSTEM_PROMPT,
        builtin_tools=builtin_tools,
    )

    if use_perplexity:

        @agent.tool_plain(
            docstring_format="google", require_parameter_descriptions=True
        )
        async def web_search(question: str) -> str:
            """Search the general web for market data, industry analysis, and external context.

            Use this tool to find:
            - Industry peer comparisons and competitor analysis
            - Analyst estimates, forecasts, and market consensus
            - Economic data (GDP growth, inflation forecasts, interest rates)
            - Tax rates and regulatory information by jurisdiction
            - Industry trends, growth projections, and market size estimates
            - Company news, recent developments, and management commentary
            - Macroeconomic context and market conditions
            - Beta calculations and market risk premiums
            - Peer group identification and benchmarking data

            DO NOT use this tool for:
            - Official company financial statements (use sec_filings_search instead)
            - Precise revenue, EBIT, or balance sheet figures (use sec_filings_search instead)
            - Exact share counts or debt levels (use sec_filings_search instead)

            Args:
                question: The question to ask in natural language. Be specific about what
                    information you need (e.g., "What is the typical EBIT margin for software
                    companies?" or "What are analyst revenue growth estimates for Tesla?").

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
                else:
                    raise ValueError(
                        f"Perplexity API returned unexpected response type from web_search. "
                        f"Expected: string content. Received: {type(response_content).__name__} "
                        f"with value: {response_content}. This indicates an API response format change."
                    )

        @agent.tool_plain(
            docstring_format="google", require_parameter_descriptions=True
        )
        async def sec_filings_search(question: str) -> str:
            """Search official SEC filings for authoritative company financial data.

            Use this tool to find OFFICIAL, AUDITED data from regulatory filings:
            - Revenue, EBIT, operating income, net income
            - Total debt, cash, shareholders' equity
            - Capital expenditures, depreciation & amortization
            - Shares outstanding (basic and diluted)
            - Historical financial performance over multiple years
            - Tax rates and effective tax rates paid
            - Management's discussion and analysis (MD&A)
            - Risk factors and business descriptions
            - Segment-level financial data
            - Cash flow statements and working capital changes

            This tool searches 10-K annual reports, 10-Q quarterly reports, 8-K current
            reports, and other official SEC filings. The data is directly from the company's
            regulatory submissions and is the most reliable source for financial metrics.

            ALWAYS use this tool when you need:
            - Exact financial figures for DCF inputs (revenue, EBIT, CapEx, etc.)
            - Historical trends from the company's own reporting
            - Official share counts and debt levels
            - Verified tax rates from actual filings

            Args:
                question: The question to ask in natural language. Include the company name
                    or ticker and specify the exact metric and time period you need
                    (e.g., "What was Apple's total revenue and EBIT for fiscal year 2023?"
                    or "What is Microsoft's total debt and cash as of their latest 10-Q?").

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
                else:
                    raise ValueError(
                        f"Perplexity API returned unexpected response type from sec_filings_search. "
                        f"Expected: string content. Received: {type(response_content).__name__} "
                        f"with value: {response_content}. This indicates an API response format change."
                    )

    return agent
