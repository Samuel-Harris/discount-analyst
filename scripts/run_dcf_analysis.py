from discount_analyst.shared.ai_models_config import ModelName
import asyncio
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import NewType

import logfire
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from discount_analyst.shared.settings import settings

from scripts.shared import ModelRunOutput, write_model_output
from discount_analyst.market_analyst.market_analyst import create_market_analyst_agent
from discount_analyst.shared.ai_models_config import AIModelsConfig
from discount_analyst.market_analyst.user_prompt import create_user_prompt
from discount_analyst.dcf_analysis.data_types import DCFAnalysisParameters
from discount_analyst.dcf_analysis.dcf_analysis import DCFAnalysis

logfire.configure(token=settings.pydantic.logfire_api_key, scrubbing=False)
logfire.instrument_pydantic_ai()

console = Console()

ResearchReport = NewType("ResearchReport", str)


class Arguments(BaseModel):
    ticker: str
    risk_free_rate: float
    research_report_path: str
    model: ModelName = ModelName.CLAUDE_OPUS_4_5


def parse_args() -> Arguments:
    parser = argparse.ArgumentParser(
        description="Run Market Analyst Agent and DCF Analysis"
    )
    parser.add_argument(
        "--ticker", type=str, required=True, help="Stock ticker symbol (e.g., AAPL)"
    )
    parser.add_argument(
        "--risk-free-rate",
        type=float,
        required=True,
        help="Risk-free rate as a decimal (e.g., 0.045)",
    )
    parser.add_argument(
        "--research-report-path",
        type=str,
        help="Path to a markdown file containing a research report",
    )
    parser.add_argument(
        "--model",
        type=ModelName,
        choices=[e.value for e in ModelName],
        default=ModelName.CLAUDE_SONNET_4_6,
        help=f"AI model to use (default: {ModelName.CLAUDE_SONNET_4_6})",
    )

    args = parser.parse_args()

    if not (0 < args.risk_free_rate <= 0.15):
        parser.error(
            f"--risk-free-rate must be a decimal between 0 and 0.15 (e.g. 0.045 for 4.5%). "
            f"Got {args.risk_free_rate}. Did you pass a percentage? Use 0.0373 for 3.73%."
        )

    return Arguments(**vars(args))


def parse_research_report(args: Arguments) -> ResearchReport:
    path = Path(args.research_report_path)
    if not path.exists():
        raise ValueError(
            f"Error: Research report file not found at {args.research_report_path}"
        )

    if not path.suffix == ".md":
        raise ValueError(
            f"Error: Research report must be a markdown file. Got {path.suffix}"
        )

    research_report_content = ResearchReport(path.read_text())
    console.log(
        f"Loaded research report from {args.research_report_path} ({len(research_report_content)} chars)"
    )

    return research_report_content


async def main():
    args = parse_args()

    research_report_content = parse_research_report(args)

    console.log(
        f"Initializing Market Analyst Agent for {args.ticker} (using {args.model} model)..."
    )

    ai_models_config = AIModelsConfig(model_name=args.model)
    agent = create_market_analyst_agent(ai_models_config)

    user_prompt = create_user_prompt(
        ticker=args.ticker, research_report=research_report_content
    )

    console.log("Running agent...")

    start = time.perf_counter()
    async with agent.run_stream(
        user_prompt,
        usage_limits=ai_models_config.market_analyst.usage_limits,
    ) as result:
        async for message in result.stream_output():
            console.log(f"Streaming: {message}")

        agent_output = await result.get_output()
        usage = result.usage()
    elapsed_s = time.perf_counter() - start
    stock_data = agent_output.stock_data
    stock_assumptions = agent_output.stock_assumptions

    # Create stock data table
    stock_table = Table(
        title=f"📈 {stock_data.name} ({stock_data.ticker}) - {stock_data.company_scale}",
        show_header=True,
        header_style="bold magenta",
    )
    stock_table.add_column("Metric", style="cyan", no_wrap=True)
    stock_table.add_column("Value", style="green", justify="right")
    stock_table.add_column("Notes")

    # Format values nicely
    current_price = stock_data.market_cap / stock_data.n_shares_outstanding
    market_cap_b = stock_data.market_cap / 1e9
    revenue_m = stock_data.revenue / 1e6
    ebit_m = stock_data.ebit / 1e6

    stock_table.add_row(
        "Current Share Price", f"${current_price:.2f}", "Implied from market cap"
    )
    stock_table.add_row(
        "Market Cap",
        f"${market_cap_b:.2f}B",
        f"Based on {stock_data.n_shares_outstanding:,.0f} shares outstanding",
    )
    stock_table.add_row(
        "Revenue (TTM)",
        f"${revenue_m:.2f}M",
        f"EBIT Margin: {stock_data.ebit_margin:.1%}",
    )
    stock_table.add_row(
        "EBIT (TTM)", f"${ebit_m:.2f}M", "Earnings Before Interest & Taxes"
    )
    stock_table.add_row(
        "Enterprise Value",
        f"${stock_data.enterprise_value / 1e9:.2f}B",
        "Market Cap + Net Debt",
    )
    stock_table.add_row(
        "Beta", f"{stock_data.beta:.2f}", "Volatility relative to market"
    )
    stock_table.add_row(
        "Interest Rate",
        f"{stock_data.implied_interest_rate:.1%}",
        "Implied cost of debt",
    )

    # Create assumptions panel
    assumptions_panel = Panel.fit(
        stock_assumptions.reasoning,
        title="🧠 Assumptions Reasoning",
        border_style="blue",
        padding=(1, 2),
    )

    # Display agent output
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold green]🤖 MARKET ANALYST AGENT OUTPUT[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(stock_table)
    console.print(assumptions_panel)

    # DCF Analysis header
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold yellow]💰 DISCOUNTED CASH FLOW ANALYSIS[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
    )

    # DCF Details panel
    dcf_details_panel = Panel.fit(
        f"Risk-free Rate: {args.risk_free_rate:.1%}\n"
        f"Forecast Period: {stock_assumptions.forecast_period_years} years\n"
        f"Terminal Growth: {stock_assumptions.assumed_perpetuity_cash_flow_growth_rate:.1%}\n"
        f"Tax Rate: {stock_assumptions.assumed_tax_rate:.1%}",
        title="📊 DCF Model Parameters",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(dcf_details_panel)

    dcf_params = DCFAnalysisParameters(
        stock_data=stock_data,
        stock_assumptions=stock_assumptions,
        risk_free_rate=args.risk_free_rate,
    )

    dcf_error: str | None = None
    try:
        dcf_analysis = DCFAnalysis(dcf_params)
        dcf_result = dcf_analysis.dcf_analysis()
    except Exception as exc:
        dcf_error = str(exc)
        dcf_result = None
        console.print(f"[yellow]DCF error: {dcf_error}[/yellow]")

    # Create DCF results table (only when DCF succeeded)
    if dcf_result is not None:
        dcf_table = Table(
            title="💎 VALUATION RESULTS", show_header=True, header_style="bold yellow"
        )
        dcf_table.add_column("Metric", style="cyan", no_wrap=True)
        dcf_table.add_column("Value", style="green", justify="right")
        dcf_table.add_column("Analysis")

        # Calculate valuation comparison
        current_price = stock_data.market_cap / stock_data.n_shares_outstanding
        intrinsic_price = dcf_result.intrinsic_share_price
        premium_discount = ((intrinsic_price - current_price) / current_price) * 100

        # Format values
        status_emoji = "📈" if premium_discount > 0 else "📉"
        status_color = "green" if premium_discount > 0 else "red"
        status_text = f"{status_emoji} [{status_color}]{premium_discount:+.1f}%[/{status_color}] vs current price"

        dcf_table.add_row(
            "Enterprise Value",
            f"${dcf_result.enterprise_value / 1e6:.2f}M",
            "Present value of projected unlevered free cash flows plus the discounted terminal value",
        )
        dcf_table.add_row(
            "Equity Value",
            f"${dcf_result.equity_value / 1e6:.2f}M",
            "Total value of shareholder equity",
        )
        dcf_table.add_row(
            "Current Market Price", f"${current_price:.2f}", "Implied from market cap"
        )
        dcf_table.add_row(
            "Intrinsic Share Value", f"${intrinsic_price:.2f}", status_text
        )

        console.print(dcf_table)

    # Write output to file (same format as model_cost_comparison)
    run_output = ModelRunOutput(
        ticker=args.ticker,
        model_name=args.model.value,
        risk_free_rate=args.risk_free_rate,
        market_analyst=agent_output,
        dcf_result=dcf_result,
        dcf_error=dcf_error,
        elapsed_s=elapsed_s,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_write_tokens=getattr(usage, "cache_write_tokens", 0),
        cache_read_tokens=getattr(usage, "cache_read_tokens", 0),
        tool_calls=getattr(usage, "tool_calls", 0),
    )
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    out_path = write_model_output(run_output, timestamp)
    console.print(f"\nSaved [dim]{out_path}[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
