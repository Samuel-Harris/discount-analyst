from discount_analyst.shared.config.ai_models_config import ModelName
import asyncio
import argparse
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import NewType

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from discount_analyst.shared.http.rate_limit_client import stream_with_retries

from scripts.shared import ModelRunOutput, write_model_output
from scripts.utils.setup_logfire import setup_logfire
from discount_analyst.appraiser.appraiser import create_appraiser_agent
from discount_analyst.shared.config.ai_models_config import AIModelsConfig
from discount_analyst.appraiser.user_prompt import create_user_prompt
from discount_analyst.dcf_analysis.data_types import DCFAnalysisParameters
from discount_analyst.dcf_analysis.dcf_analysis import DCFAnalysis
from discount_analyst.appraiser.data_types import AppraiserOutput
from discount_analyst.dcf_analysis.data_types import DCFAnalysisResult

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_OUTPUTS_DIR = _PROJECT_ROOT / "outputs"

setup_logfire()

console = Console()

ResearchReport = NewType("ResearchReport", str)

# Ticker: 1-10 chars, starts with A-Z, only letters, digits, dots (e.g. AAPL, BRK.B)
_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.]{0,9}$")


@dataclass(frozen=True)
class TickerReportPair:
    ticker: str
    research_report_path: str


@dataclass
class SharedArgs:
    risk_free_rate: float
    model: ModelName


def _validate_pair(raw: str, parser: argparse.ArgumentParser) -> TickerReportPair:
    """Parse and validate a TICKER:PATH pair. Catches common swap mistakes."""
    if ":" not in raw:
        parser.error(
            f"Invalid pair '{raw}': expected TICKER:PATH (e.g. AAPL:reports/aapl.md). "
            "Use a colon to separate ticker from path."
        )
    parts = raw.split(":", 1)
    if len(parts) != 2:
        parser.error(f"Invalid pair '{raw}': expected exactly one colon.")
    first, second = parts[0].strip(), parts[1].strip()
    if not first or not second:
        parser.error(f"Invalid pair '{raw}': ticker and path must be non-empty.")

    # Detect likely swap: first part looks like a path
    if "/" in first or "\\" in first or first.endswith(".md"):
        parser.error(
            f"Invalid pair '{raw}': the first part looks like a path. "
            f"Did you mean --pair {second}:{first}? Format is TICKER:PATH (e.g. AAPL:reports/aapl.md)."
        )

    # Second part must look like a path and end in .md
    if not second.endswith(".md"):
        hint = ""
        if _TICKER_RE.match(second):
            hint = (
                " The second part looks like a ticker; did you swap ticker and path? "
            )
        parser.error(
            f"Invalid pair '{raw}': path must be a .md file. Got '{second}'.{hint}"
            "Format is TICKER:PATH (e.g. AAPL:reports/aapl.md)."
        )

    # First part must look like a ticker (uppercase, alphanumeric + dots)
    if not _TICKER_RE.match(first):
        parser.error(
            f"Invalid pair '{raw}': ticker must be 1-10 chars, start with A-Z, "
            f"only A-Z, 0-9, dots (e.g. AAPL, BRK.B). Got '{first}'."
        )

    path = Path(second)
    if not path.exists():
        parser.error(
            f"Invalid pair '{raw}': research report file not found at '{second}'."
        )

    return TickerReportPair(ticker=first, research_report_path=second)


def parse_args() -> tuple[list[TickerReportPair], SharedArgs]:
    parser = argparse.ArgumentParser(
        description="Run Market Analyst Agent and DCF Analysis"
    )
    parser.add_argument(
        "--pair",
        action="append",
        metavar="TICKER:PATH",
        required=True,
        help="Ticker and research report path (repeatable). E.g. --pair AAPL:reports/aapl.md --pair MSFT:reports/msft.md",
    )
    parser.add_argument(
        "--risk-free-rate",
        type=float,
        required=True,
        help="Risk-free rate as a decimal (e.g., 0.045)",
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

    pairs = [_validate_pair(p, parser) for p in args.pair]
    shared = SharedArgs(risk_free_rate=args.risk_free_rate, model=args.model)
    return pairs, shared


def load_research_report(path: Path) -> ResearchReport:
    """Load and validate a research report from path."""
    if not path.exists():
        raise ValueError(f"Research report file not found at {path}")
    if path.suffix != ".md":
        raise ValueError(f"Research report must be a markdown file. Got {path.suffix}")
    content = ResearchReport(path.read_text())
    console.log(f"Loaded research report from {path} ({len(content)} chars)")
    return content


@dataclass
class AgentRunResult:
    output: AppraiserOutput
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int


@dataclass
class PairRunArgs:
    """Args for running analysis on a single ticker/report pair."""

    ticker: str
    research_report_path: str
    risk_free_rate: float
    model: ModelName


def _pair_run_args(pair: TickerReportPair, shared: SharedArgs) -> PairRunArgs:
    """Build run args for a single pair (used by run_agent, run_dcf_and_display, save_run_output)."""
    return PairRunArgs(
        ticker=pair.ticker,
        research_report_path=pair.research_report_path,
        risk_free_rate=shared.risk_free_rate,
        model=shared.model,
    )


async def run_agent(
    args: PairRunArgs,
    research_report_content: ResearchReport,
    *,
    use_perplexity: bool = True,
) -> AgentRunResult:
    """Run the Market Analyst agent and return output with usage stats."""
    ai_models_config = AIModelsConfig(model_name=args.model)
    agent = create_appraiser_agent(ai_models_config, use_perplexity=use_perplexity)
    user_prompt = create_user_prompt(
        ticker=args.ticker, research_report=research_report_content
    )

    start = time.perf_counter()
    async with stream_with_retries(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=ai_models_config.model.usage_limits,
    ) as result:
        async for message in result.stream_output():
            console.log(f"Streaming: {message}")
        agent_output = await result.get_output()
        usage = result.usage()
    elapsed_s = time.perf_counter() - start

    return AgentRunResult(
        output=agent_output,
        elapsed_s=elapsed_s,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_write_tokens=getattr(usage, "cache_write_tokens", 0),
        cache_read_tokens=getattr(usage, "cache_read_tokens", 0),
        tool_calls=getattr(usage, "tool_calls", 0),
    )


def build_stock_table(output: AppraiserOutput) -> Table:
    """Build a Rich table from the agent's stock data."""
    stock_data = output.stock_data
    current_price = stock_data.market_cap / stock_data.n_shares_outstanding
    market_cap_b = stock_data.market_cap / 1e9
    revenue_m = stock_data.revenue / 1e6
    ebit_m = stock_data.ebit / 1e6

    table = Table(
        title=f"📈 {stock_data.name} ({stock_data.ticker}) - {stock_data.company_scale}",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green", justify="right")
    table.add_column("Notes")
    table.add_row(
        "Current Share Price", f"${current_price:.2f}", "Implied from market cap"
    )
    table.add_row(
        "Market Cap",
        f"${market_cap_b:.2f}B",
        f"Based on {stock_data.n_shares_outstanding:,.0f} shares outstanding",
    )
    table.add_row(
        "Revenue (TTM)",
        f"${revenue_m:.2f}M",
        f"EBIT Margin: {stock_data.ebit_margin:.1%}",
    )
    table.add_row("EBIT (TTM)", f"${ebit_m:.2f}M", "Earnings Before Interest & Taxes")
    table.add_row(
        "Enterprise Value",
        f"${stock_data.enterprise_value / 1e9:.2f}B",
        "Market Cap + Net Debt",
    )
    table.add_row("Beta", f"{stock_data.beta:.2f}", "Volatility relative to market")
    table.add_row(
        "Interest Rate",
        f"{stock_data.implied_interest_rate:.1%}",
        "Implied cost of debt",
    )
    return table


def display_agent_output(output: AppraiserOutput) -> None:
    """Print the Market Analyst agent output section."""
    stock_table = build_stock_table(output)
    assumptions_panel = Panel.fit(
        output.stock_assumptions.reasoning,
        title="🧠 Assumptions Reasoning",
        border_style="blue",
        padding=(1, 2),
    )
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


def run_dcf_and_display(
    args: PairRunArgs, agent_output: AppraiserOutput
) -> tuple[DCFAnalysisResult | None, str | None]:
    """Run DCF analysis and display results. Returns (dcf_result, dcf_error)."""
    stock_data = agent_output.stock_data
    stock_assumptions = agent_output.stock_assumptions

    console.print("\n")
    console.print(
        Panel.fit(
            "[bold yellow]💰 DISCOUNTED CASH FLOW ANALYSIS[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
    )
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
    dcf_result: DCFAnalysisResult | None = None
    try:
        dcf_analysis = DCFAnalysis(dcf_params)
        dcf_result = dcf_analysis.dcf_analysis()
    except Exception as exc:
        dcf_error = str(exc)
        console.print(f"[yellow]DCF error: {dcf_error}[/yellow]")

    if dcf_result is not None:
        current_price = stock_data.market_cap / stock_data.n_shares_outstanding
        intrinsic_price = dcf_result.intrinsic_share_price
        premium_discount = ((intrinsic_price - current_price) / current_price) * 100
        status_emoji = "📈" if premium_discount > 0 else "📉"
        status_color = "green" if premium_discount > 0 else "red"
        status_text = f"{status_emoji} [{status_color}]{premium_discount:+.1f}%[/{status_color}] vs current price"

        dcf_table = Table(
            title="💎 VALUATION RESULTS", show_header=True, header_style="bold yellow"
        )
        dcf_table.add_column("Metric", style="cyan", no_wrap=True)
        dcf_table.add_column("Value", style="green", justify="right")
        dcf_table.add_column("Analysis")
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

    return dcf_result, dcf_error


def save_run_output(
    args: PairRunArgs,
    agent_output: AppraiserOutput,
    agent_result: AgentRunResult,
    dcf_result: DCFAnalysisResult | None,
    dcf_error: str | None,
) -> Path:
    """Build ModelRunOutput, write to outputs/, and return the path."""
    run_output = ModelRunOutput(
        ticker=args.ticker,
        model_name=args.model.value,
        risk_free_rate=args.risk_free_rate,
        appraiser=agent_output,
        dcf_result=dcf_result,
        dcf_error=dcf_error,
        elapsed_s=agent_result.elapsed_s,
        input_tokens=agent_result.input_tokens,
        output_tokens=agent_result.output_tokens,
        cache_write_tokens=agent_result.cache_write_tokens,
        cache_read_tokens=agent_result.cache_read_tokens,
        tool_calls=agent_result.tool_calls,
    )
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    return write_model_output(
        run_output=run_output,
        timestamp=timestamp,
        output_dir=_OUTPUTS_DIR,
    )


async def run_one_pair(pair: TickerReportPair, shared: SharedArgs) -> None:
    """Run analysis for a single ticker/report pair."""
    args = _pair_run_args(pair, shared)
    research_report_content = load_research_report(Path(args.research_report_path))

    console.log(
        f"Initializing Appraiser Agent for {args.ticker} (using {args.model} model)..."
    )
    console.log("Running agent...")
    agent_result = await run_agent(args, research_report_content)

    display_agent_output(agent_result.output)
    dcf_result, dcf_error = run_dcf_and_display(args, agent_result.output)

    out_path = save_run_output(
        args, agent_result.output, agent_result, dcf_result, dcf_error
    )
    console.print(f"\nSaved [dim]{out_path}[/dim]")


async def main():
    pairs, shared = parse_args()

    for i, pair in enumerate(pairs):
        if len(pairs) > 1 and i > 0:
            console.print("\n[bold]─── Next pair ───[/bold]\n")
        await run_one_pair(pair, shared)


if __name__ == "__main__":
    asyncio.run(main())
