"""Agent-specific tool descriptions for Perplexity-backed search tools."""

from dataclasses import dataclass

from discount_analyst.agents.common.agent_names import AgentName


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
    AgentName.SURVEYOR: PerplexityToolDescriptions(
        web_search="""Search the general web to discover and qualify small-cap equity candidates (UK and US).

Use this tool to find:
- Thematic ideas, sectors, and industries where under-covered names may trade cheaply
- Recent news, controversies, and red flags for specific tickers or companies
- Business models, competitive positioning, and qualitative context beyond raw screens
- Analyst commentary, media coverage frequency, and signals about sell-side coverage depth
- UK-listed stocks: RNS announcements (e.g. Director/PDMR dealing, material events)
- Liquidity, exchange listing, and operating-history clues when MCP data is incomplete

Prefer FMP/EODHD MCP tools for repeatable numeric screens (market cap, ratios, statements).
Use this tool to broaden the funnel, stress-test narratives, and fill UK gaps where filings tools
are weaker.

DO NOT rely on this tool alone for:
- Precise audited line items for US names when SEC filings search can answer (use sec_filings_search)

Args:
    question: A natural-language question naming the company, ticker, or theme and what you need
        (e.g. "Recent RNS director dealings for [UK ticker] in the last 6 months" or
        "News and controversies for [US small-cap] in the last year").

Returns:
    Answers and synthesis based on web sources.""",
        sec_filings_search="""Search official SEC filings for US-listed companies only.

Use this tool to verify and deepen screening for NASDAQ/NYSE names:
- 10-K and 10-Q disclosures vs claims from financial data endpoints
- Form 4 insider buying and selling patterns
- 8-K material events and proxy / governance disclosures
- Risk factors, MD&A, and segment detail from regulatory text

This is not the primary tool for UK/LSE/AIM names (use web_search and EODHD fundamentals).

Args:
    question: Include ticker or company name and the filing angle (e.g. "Summarize insider
        open-market purchases on Form 4 for [ticker] in the last 6 months" or
        "From the latest 10-K, what does [ticker] disclose about debt maturities and liquidity?").

Returns:
    The answer based on SEC filings.""",
    ),
    AgentName.RESEARCHER: PerplexityToolDescriptions(
        web_search="""Search the general web for neutral evidence on business quality, market framing, and catalysts.

Use this tool to find:
- Recent management commentary, interviews, and investor communication
- Industry reports, competitor moves, and demand-side signals
- News flow that could alter expectations (customers, regulation, products)
- Media and sell-side framing to build the current market narrative
- Coverage quality signals (who is paying attention and what they emphasize)
- Margin and growth context from peers or sector data sources

Do not use this tool for:
- Precise audited financial statement line items when SEC filings are available
- Recommendations, valuation calls, or target prices as final conclusions

Args:
    question: A specific natural-language question describing the exact evidence
        you need and the relevant company/ticker.

Returns:
    Evidence and synthesis based on web sources.""",
        sec_filings_search="""Search SEC filings for authoritative, company-reported facts.

Use this tool to verify:
- Revenue composition, segment trends, and profitability disclosures
- Balance sheet, debt, liquidity, and cash flow statement details
- Risk factors, legal contingencies, and governance disclosures
- Management discussion and known uncertainties from 10-K/10-Q filings
- Share count and capital allocation details from official filings

This tool is the preferred source for factual claims tied to US-listed companies.
Use it to close or refine data gaps identified by Surveyor.

Args:
    question: A specific question that includes company/ticker, metric/disclosure,
        and desired period (e.g. latest 10-K or most recent 10-Q).

Returns:
    Evidence extracted from SEC filings.""",
    ),
}
