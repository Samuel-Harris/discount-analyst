"""Agent-specific tool descriptions for Perplexity-backed search tools."""

from dataclasses import dataclass

from discount_analyst.shared.constants.agents import AgentName


@dataclass(frozen=True)
class PerplexityToolDescriptions:
    """Docstrings for web_search and sec_filings_search tools per agent."""

    web_search: str
    sec_filings_search: str


AGENT_TOOL_DESCRIPTIONS: dict[AgentName, PerplexityToolDescriptions] = {
    AgentName.APPRAISER: PerplexityToolDescriptions(
        web_search="""Search the general web for market data, industry analysis, and external context.

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
    The answer to the question based on web sources.""",
        sec_filings_search="""Search official SEC filings for authoritative company financial data.

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
    The answer to the question based on SEC filings.""",
    ),
}
