"""Run the Appraiser agent and DCF from Sentinel run output JSON selectors."""

import argparse
import asyncio
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from pydantic import BaseModel, ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from discount_analyst.agents.appraiser.appraiser import create_appraiser_agent
from discount_analyst.agents.appraiser.schema import AppraiserInput, AppraiserOutput
from discount_analyst.agents.appraiser.user_prompt import create_user_prompt
from discount_analyst.valuation.data_types import (
    DCFAnalysisParameters,
    DCFAnalysisResult,
)
from discount_analyst.valuation.dcf_analysis import DCFAnalysis
from discount_analyst.config.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.agents.common.streamed_agent_run import run_streamed_agent
from discount_analyst.agents.surveyor.schema import SurveyorCandidate

from backend.contracts.stock_run_args import StockRunArgs

from scripts.common.cli import (
    DEFAULT_AGENT_CLI_DEFAULTS,
    add_agent_cli_model_argument,
    add_agent_cli_web_search_arguments,
)
from scripts.common.artefacts import write_agent_json
from scripts.common.run_outputs import (
    AppraiserRunOutput,
    ResearcherRunOutput,
    SentinelRunOutput,
    StrategistRunOutput,
    SurveyorRunOutput,
    TurnUsage,
)
from scripts.common.usage import extract_turn_usage
from scripts.utils.setup_logfire import setup_logfire

setup_logfire()

console = Console()


@dataclass(frozen=True)
class Selector:
    sentinel_report_path: Path
    ticker: str | None
    raw: str


class AppraiserTarget(NamedTuple):
    sentinel_report_path: Path
    sentinel_run: SentinelRunOutput
    appraiser_input: AppraiserInput


@dataclass
class SharedArgs:
    risk_free_rate: float
    model: ModelName
    use_perplexity: bool
    use_mcp_financial_data: bool


class AppraiserCliArgs(BaseModel):
    model: ModelName
    selectors: list[Selector]
    risk_free_rate: float
    use_perplexity: bool
    use_mcp_financial_data: bool


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


def _parse_selector(raw: str, parser: argparse.ArgumentParser) -> Selector:
    stripped = raw.strip()
    if not stripped:
        parser.error(
            "Invalid --sentinel-report-and-ticker value: empty selector. "
            "Expected '<sentinel_run_output.json>' or "
            "'<sentinel_run_output.json>:<TICKER>'."
        )

    report_part: str
    ticker_part: str | None
    if ":" in stripped:
        report_part, ticker_part = stripped.rsplit(":", maxsplit=1)
        report_part = report_part.strip()
        ticker_part = ticker_part.strip()
        if not report_part or not ticker_part:
            parser.error(
                f"Invalid selector '{raw}'. Expected "
                "'<sentinel_run_output.json>' or "
                "'<sentinel_run_output.json>:<TICKER>'."
            )
    else:
        report_part = stripped
        ticker_part = None

    path = Path(report_part).expanduser().resolve()
    if path.suffix.lower() != ".json":
        parser.error(
            f"Invalid selector '{raw}': expected a .json Sentinel run artefact path. "
            f"Got: {path}."
        )
    if not path.is_file():
        parser.error(
            f"Invalid selector '{raw}': Sentinel output file not found at {path}. "
            "Expected '<sentinel_run_output.json>' or "
            "'<sentinel_run_output.json>:<TICKER>'."
        )

    return Selector(sentinel_report_path=path, ticker=ticker_part, raw=raw)


def parse_args() -> AppraiserCliArgs:
    parser = argparse.ArgumentParser(
        description=(
            "Run Appraiser agent and DCF for one or more Sentinel run output JSON files."
        )
    )
    parser.add_argument(
        "--sentinel-report-and-ticker",
        action="append",
        required=True,
        dest="selectors",
        metavar="SELECTOR",
        help=(
            "Sentinel artefact selector (repeatable): either "
            "'<sentinel_run_output.json>' for that run "
            "or '<sentinel_run_output.json>:<TICKER>' to require a ticker match."
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

    raw = parser.parse_args()

    if not (0 < raw.risk_free_rate <= 0.15):
        parser.error(
            f"--risk-free-rate must be a decimal between 0 and 0.15 (e.g. 0.045 for 4.5%%). "
            f"Got {raw.risk_free_rate}."
        )

    selectors = [_parse_selector(value, parser) for value in raw.selectors]
    return AppraiserCliArgs(
        model=raw.model,
        selectors=selectors,
        risk_free_rate=raw.risk_free_rate,
        use_perplexity=raw.use_perplexity,
        use_mcp_financial_data=not raw.no_mcp,
    )


def _load_sentinel_run_output(path: Path) -> SentinelRunOutput:
    try:
        return SentinelRunOutput.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise ValueError(
            f"Invalid Sentinel run output JSON shape at {path}: {exc}"
        ) from exc


def _load_surveyor_run_output(path: Path) -> SurveyorRunOutput:
    try:
        return SurveyorRunOutput.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise ValueError(
            f"Invalid Surveyor run output JSON shape at {path}: {exc}"
        ) from exc


def _load_researcher_run_output(path: Path) -> ResearcherRunOutput:
    try:
        return ResearcherRunOutput.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise ValueError(
            f"Invalid Researcher run output JSON shape at {path}: {exc}"
        ) from exc


def _load_strategist_run_output(path: Path) -> StrategistRunOutput:
    try:
        return StrategistRunOutput.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise ValueError(
            f"Invalid Strategist run output JSON shape at {path}: {exc}"
        ) from exc


def _resolve_target(selector: Selector, *, risk_free_rate: float) -> AppraiserTarget:
    sent = _load_sentinel_run_output(selector.sentinel_report_path)
    if selector.ticker is not None:
        ticker_folded = selector.ticker.casefold()
        if sent.ticker.casefold() != ticker_folded:
            raise ValueError(
                f"Ticker '{selector.ticker}' does not match Sentinel artefact "
                f"{selector.sentinel_report_path} (ticker={sent.ticker})."
            )

    surveyor_path = Path(sent.source_surveyor_report).expanduser().resolve()
    researcher_path = Path(sent.source_researcher_report).expanduser().resolve()
    strategist_path = Path(sent.source_strategist_report).expanduser().resolve()
    for label, p in (
        ("Surveyor", surveyor_path),
        ("Researcher", researcher_path),
        ("Strategist", strategist_path),
    ):
        if not p.is_file():
            raise ValueError(
                f"Sentinel artefact {selector.sentinel_report_path} references "
                f"{label} report that is not a file: {p}"
            )

    surveyor = _load_surveyor_run_output(surveyor_path)
    idx = sent.source_candidate_index
    if idx < 0 or idx >= len(surveyor.output.candidates):
        raise ValueError(
            f"Sentinel artefact {selector.sentinel_report_path} references "
            f"candidate_index={idx} but Surveyor report has "
            f"{len(surveyor.output.candidates)} candidates ({surveyor_path})."
        )
    surveyor_candidate = surveyor.output.candidates[idx]

    researcher = _load_researcher_run_output(researcher_path)
    strategist = _load_strategist_run_output(strategist_path)

    appraiser_input = AppraiserInput(
        stock_candidate=surveyor_candidate,
        deep_research=researcher.output,
        thesis=strategist.output,
        evaluation=sent.output,
        risk_free_rate=risk_free_rate,
    )

    return AppraiserTarget(
        sentinel_report_path=selector.sentinel_report_path,
        sentinel_run=sent,
        appraiser_input=appraiser_input,
    )


def resolve_targets(
    selectors: list[Selector], *, risk_free_rate: float
) -> list[AppraiserTarget]:
    return [_resolve_target(s, risk_free_rate=risk_free_rate) for s in selectors]


def _build_suffixes(targets: list[AppraiserTarget]) -> list[str]:
    ticker_counts = Counter(t.sentinel_run.ticker.casefold() for t in targets)
    ticker_seen: Counter[str] = Counter()
    suffixes: list[str] = []

    for target in targets:
        folded = target.sentinel_run.ticker.casefold()
        ticker_seen[folded] += 1
        if ticker_counts[folded] > 1:
            suffixes.append(
                f"{target.sentinel_run.ticker.upper()}-{ticker_seen[folded]}"
            )
        else:
            suffixes.append(target.sentinel_run.ticker.upper())
    return suffixes


def _stock_run_args(candidate: SurveyorCandidate, shared: SharedArgs) -> StockRunArgs:
    return StockRunArgs(
        surveyor_candidate=candidate,
        risk_free_rate=shared.risk_free_rate,
        model=shared.model,
    )


async def run_agent(
    args: StockRunArgs,
    appraiser_input: AppraiserInput,
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
    user_prompt = create_user_prompt(appraiser_input=appraiser_input)

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
    *,
    source_surveyor_report: str,
    source_candidate_index: int,
    source_researcher_report: str,
    source_strategist_report: str,
    source_sentinel_report: str,
    filename_suffix: str | None = None,
) -> Path:
    """Build ``AppraiserRunOutput``, write JSON via ``write_agent_json``, return path."""
    suffix = filename_suffix or args.surveyor_candidate.ticker.upper()
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
        source_surveyor_report=source_surveyor_report,
        source_candidate_index=source_candidate_index,
        source_researcher_report=source_researcher_report,
        source_strategist_report=source_strategist_report,
        source_sentinel_report=source_sentinel_report,
    )
    return write_agent_json(
        payload=run_output,
        model_name=args.model,
        agent_name=AgentName.APPRAISER,
        filename_suffix=suffix,
    )


async def main() -> None:
    cli = parse_args()
    shared = SharedArgs(
        risk_free_rate=cli.risk_free_rate,
        model=cli.model,
        use_perplexity=cli.use_perplexity,
        use_mcp_financial_data=cli.use_mcp_financial_data,
    )
    targets = resolve_targets(cli.selectors, risk_free_rate=cli.risk_free_rate)
    if not targets:
        raise SystemExit("No Sentinel artefacts selected to run Appraiser.")

    suffixes = _build_suffixes(targets)

    for i, target in enumerate(targets):
        if i > 0:
            console.print("\n[bold]─── Next target ───[/bold]\n")

        sent = target.sentinel_run
        if suffixes[i] != sent.ticker.upper():
            console.print(
                f"[yellow]Duplicate ticker '{sent.ticker}' detected; "
                f"using output suffix '{suffixes[i]}'.[/yellow]"
            )

        candidate = target.appraiser_input.stock_candidate
        stock_args = _stock_run_args(candidate, shared)

        console.log(
            f"Initializing Appraiser Agent for {candidate.ticker} "
            f"(source={target.sentinel_report_path}, using {shared.model} model)..."
        )
        console.log("Running agent...")
        agent_result = await run_agent(
            stock_args,
            target.appraiser_input,
            use_perplexity=shared.use_perplexity,
            use_mcp_financial_data=shared.use_mcp_financial_data,
        )

        display_agent_output(agent_result.output)
        dcf_result, dcf_error = run_dcf_and_display(stock_args, agent_result.output)

        out_path = save_run_output(
            stock_args,
            agent_result.output,
            agent_result,
            dcf_result,
            dcf_error,
            source_surveyor_report=sent.source_surveyor_report,
            source_candidate_index=sent.source_candidate_index,
            source_researcher_report=sent.source_researcher_report,
            source_strategist_report=sent.source_strategist_report,
            source_sentinel_report=str(target.sentinel_report_path.resolve()),
            filename_suffix=suffixes[i],
        )
        console.print(f"\nSaved [dim]{out_path}[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
