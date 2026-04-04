"""Run the Appraiser agent and DCF valuation for stock research folders."""

import argparse
import asyncio
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import NewType

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from discount_analyst.agents.appraiser.appraiser import create_appraiser_agent
from discount_analyst.agents.appraiser.user_prompt import create_user_prompt
from discount_analyst.shared.schemas.appraiser import AppraiserOutput
from discount_analyst.dcf_analysis.data_types import (
    DCFAnalysisParameters,
    DCFAnalysisResult,
)
from discount_analyst.dcf_analysis.dcf_analysis import DCFAnalysis
from discount_analyst.shared.config.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.shared.constants.agents import AgentName
from discount_analyst.shared.ai.streamed_agent_run import run_streamed_agent
from discount_analyst.shared.schemas.surveyor import SurveyorCandidate

from scripts.shared.cli import (
    DEFAULT_AGENT_CLI_DEFAULTS,
    add_agent_cli_model_argument,
    add_agent_cli_web_search_arguments,
)
from scripts.shared.outputs import write_agent_json
from scripts.shared.schemas.run_outputs import AppraiserRunOutput, TurnUsage
from scripts.shared.usage import extract_turn_usage
from scripts.utils.setup_logfire import setup_logfire

setup_logfire()

console = Console()

ResearchReport = NewType("ResearchReport", str)

DEEP_RESEARCH_FILENAME = "deep-research.md"
SURVEYOR_REPORT_FILENAME = "surveyor-report.json"


@dataclass(frozen=True)
class StockResearchDir:
    """A directory containing deep-research.md and surveyor-report.json."""

    dir_path: Path


@dataclass
class SharedArgs:
    risk_free_rate: float
    model: ModelName
    use_perplexity: bool
    use_mcp_financial_data: bool


def _validate_stock_dir(raw: str, parser: argparse.ArgumentParser) -> StockResearchDir:
    """Resolve a stock folder and ensure required files exist."""
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        parser.error(f"Invalid --dir '{raw}': not a directory (resolved: {path}).")

    md = path / DEEP_RESEARCH_FILENAME
    sj = path / SURVEYOR_REPORT_FILENAME
    if not md.is_file():
        parser.error(
            f"Invalid --dir '{raw}': missing {DEEP_RESEARCH_FILENAME!r} "
            f"(expected at {md})."
        )
    if md.suffix.lower() != ".md":
        parser.error(
            f"Invalid --dir '{raw}': research file must be markdown (.md). Got {md}."
        )
    if not sj.is_file():
        parser.error(
            f"Invalid --dir '{raw}': missing {SURVEYOR_REPORT_FILENAME!r} "
            f"(expected at {sj})."
        )

    return StockResearchDir(dir_path=path)


def parse_args() -> tuple[list[StockResearchDir], SharedArgs]:
    parser = argparse.ArgumentParser(description="Run Appraiser agent and DCF analysis")
    parser.add_argument(
        "--dir",
        action="append",
        dest="stock_dirs",
        metavar="PATH",
        required=True,
        help=(
            "Stock research folder (repeatable). Each directory must contain "
            f"{DEEP_RESEARCH_FILENAME!r} and {SURVEYOR_REPORT_FILENAME!r}. "
            "Ticker is taken from the surveyor JSON."
        ),
    )
    parser.add_argument(
        "--risk-free-rate",
        type=float,
        required=True,
        help="Risk-free rate as a decimal (e.g., 0.045)",
    )
    add_agent_cli_model_argument(parser)
    add_agent_cli_web_search_arguments(parser)
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help=(
            "Do not register EODHD/FMP MCP toolsets (required for Google models; "
            "optional for Anthropic/OpenAI)."
        ),
    )

    args = parser.parse_args()

    if not (0 < args.risk_free_rate <= 0.15):
        parser.error(
            f"--risk-free-rate must be a decimal between 0 and 0.15 (e.g. 0.045 for 4.5%). "
            f"Got {args.risk_free_rate}. Did you pass a percentage? Use 0.0373 for 3.73%."
        )

    stock_dirs = [_validate_stock_dir(d, parser) for d in args.stock_dirs]
    shared = SharedArgs(
        risk_free_rate=args.risk_free_rate,
        model=args.model,
        use_perplexity=args.use_perplexity,
        use_mcp_financial_data=not args.no_mcp,
    )
    return stock_dirs, shared


def load_research_report(path: Path) -> ResearchReport:
    """Load and validate a research report from path."""
    if not path.exists():
        raise ValueError(f"Research report file not found at {path}")
    if path.suffix != ".md":
        raise ValueError(f"Research report must be a markdown file. Got {path.suffix}")
    content = ResearchReport(path.read_text())
    console.log(f"Loaded research report from {path} ({len(content)} chars)")
    return content


def load_surveyor_candidate(path: Path) -> SurveyorCandidate:
    """Parse ``surveyor-report.json`` as a single ``SurveyorCandidate``."""
    return SurveyorCandidate.model_validate_json(path.read_text())


def _ticker_appears_in_research_report(*, ticker: str, report: str) -> bool:
    """True if ``ticker`` appears case-insensitively in ``report``."""
    stripped = ticker.strip()
    if not stripped:
        return False
    return stripped.casefold() in report.casefold()


def _confirm_if_ticker_missing_from_report(
    *,
    ticker: str,
    report: str,
    dir_path: Path,
) -> None:
    """Prompt or exit when the surveyor ticker is absent from the deep-research body."""
    if _ticker_appears_in_research_report(ticker=ticker, report=report):
        return

    console.print(
        f"[yellow]Warning:[/yellow] Ticker [bold]{ticker}[/bold] from "
        f"{SURVEYOR_REPORT_FILENAME} does not appear in {DEEP_RESEARCH_FILENAME} "
        f"under {dir_path}."
    )
    if not sys.stdin.isatty():
        console.print(
            "[red]Non-interactive terminal: cannot confirm. Ensure the ticker appears in "
            f"{DEEP_RESEARCH_FILENAME}, or run from an interactive terminal.[/red]"
        )
        raise SystemExit(1)
    answer = input("Continue anyway? [y/N]: ").strip().lower()
    if answer not in ("y", "yes"):
        console.print("[red]Aborted.[/red]")
        raise SystemExit(1)


@dataclass
class AgentRunResult:
    output: AppraiserOutput
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    turn_usage: list[TurnUsage]


@dataclass
class StockRunArgs:
    """Args for running analysis on a single stock research directory."""

    stock_dir: Path
    surveyor_candidate: SurveyorCandidate
    risk_free_rate: float
    model: ModelName


def _stock_run_args(
    stock: StockResearchDir,
    candidate: SurveyorCandidate,
    shared: SharedArgs,
) -> StockRunArgs:
    """Build run args for one stock folder (run_agent, DCF, save_run_output)."""
    return StockRunArgs(
        stock_dir=stock.dir_path,
        surveyor_candidate=candidate,
        risk_free_rate=shared.risk_free_rate,
        model=shared.model,
    )


async def run_agent(
    args: StockRunArgs,
    research_report_content: ResearchReport,
    *,
    use_perplexity: bool = DEFAULT_AGENT_CLI_DEFAULTS.use_perplexity,
    use_mcp_financial_data: bool = True,
) -> AgentRunResult:
    """Run the Appraiser agent and return output with usage stats."""
    ai_models_config = AIModelsConfig(model_name=args.model)
    agent = create_appraiser_agent(
        ai_models_config,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
    )
    user_prompt = create_user_prompt(
        ticker=args.surveyor_candidate.ticker,
        research_report=research_report_content,
        surveyor_candidate=args.surveyor_candidate,
    )

    start = time.perf_counter()
    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
    )
    agent_output = outcome.output
    usage = outcome.usage
    turn_usage = extract_turn_usage(outcome.all_messages)

    for turn in turn_usage:
        console.log(
            f"Turn {turn.turn} usage: in={turn.input_tokens} "
            f"out={turn.output_tokens} total={turn.total_tokens} "
            f"(cum_in={turn.cumulative_input_tokens} "
            f"cum_out={turn.cumulative_output_tokens})"
        )
    elapsed_s = time.perf_counter() - start

    return AgentRunResult(
        output=agent_output,
        elapsed_s=elapsed_s,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_write_tokens=getattr(usage, "cache_write_tokens", 0),
        cache_read_tokens=getattr(usage, "cache_read_tokens", 0),
        tool_calls=getattr(usage, "tool_calls", 0),
        turn_usage=turn_usage,
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
    """Print the Appraiser agent output section."""
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
            "[bold green]🤖 APPRAISER AGENT OUTPUT[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(stock_table)
    console.print(assumptions_panel)


def run_dcf_and_display(
    args: StockRunArgs, agent_output: AppraiserOutput
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
    args: StockRunArgs,
    agent_output: AppraiserOutput,
    agent_result: AgentRunResult,
    dcf_result: DCFAnalysisResult | None,
    dcf_error: str | None,
) -> Path:
    """Build ``AppraiserRunOutput``, write JSON via ``write_agent_json``, return path."""
    run_output = AppraiserRunOutput(
        ticker=args.surveyor_candidate.ticker,
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
        turn_usage=agent_result.turn_usage,
    )
    return write_agent_json(
        payload=run_output,
        model_name=args.model,
        agent_name=AgentName.APPRAISER,
        filename_suffix=args.surveyor_candidate.ticker.upper(),
    )


async def run_one_stock(stock: StockResearchDir, shared: SharedArgs) -> None:
    """Run analysis for a single stock research directory."""
    deep_research_path = stock.dir_path / DEEP_RESEARCH_FILENAME
    surveyor_report_path = stock.dir_path / SURVEYOR_REPORT_FILENAME
    candidate = load_surveyor_candidate(surveyor_report_path)
    args = _stock_run_args(stock, candidate, shared)
    research_report_content = load_research_report(deep_research_path)
    _confirm_if_ticker_missing_from_report(
        ticker=candidate.ticker,
        report=str(research_report_content),
        dir_path=stock.dir_path,
    )

    console.log(
        f"Initializing Appraiser Agent for {args.surveyor_candidate.ticker} "
        f"(using {args.model} model)..."
    )
    console.log("Running agent...")
    agent_result = await run_agent(
        args,
        research_report_content,
        use_perplexity=shared.use_perplexity,
        use_mcp_financial_data=shared.use_mcp_financial_data,
    )

    display_agent_output(agent_result.output)
    dcf_result, dcf_error = run_dcf_and_display(args, agent_result.output)

    out_path = save_run_output(
        args, agent_result.output, agent_result, dcf_result, dcf_error
    )
    console.print(f"\nSaved [dim]{out_path}[/dim]")


async def main():
    stock_dirs, shared = parse_args()

    for i, stock in enumerate(stock_dirs):
        if len(stock_dirs) > 1 and i > 0:
            console.print("\n[bold]─── Next stock ───[/bold]\n")
        await run_one_stock(stock, shared)


if __name__ == "__main__":
    asyncio.run(main())
