"""Run Surveyor or Profiler entry, then Researcher through Sentinel, gated Appraiser + DCF, Arbiter, Verdicts."""

import argparse
import asyncio
from collections import Counter
from dataclasses import dataclass, replace
from datetime import date

from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from discount_analyst.agents.arbiter.arbiter import create_arbiter_agent
from discount_analyst.agents.arbiter.schema import (
    ArbiterDecision,
    ArbiterInput,
    ValuationResult,
)
from discount_analyst.agents.arbiter.user_prompt import (
    create_user_prompt as create_arbiter_user_prompt,
)
from discount_analyst.agents.sentinel.schema import (
    EvaluationReport,
    sentinel_proceeds_to_valuation,
)
from discount_analyst.agents.sentinel.sentinel import create_sentinel_agent
from discount_analyst.agents.sentinel.user_prompt import (
    create_user_prompt as create_sentinel_user_prompt,
)
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.agents.common.streamed_agent_run import run_streamed_agent
from discount_analyst.agents.researcher.researcher import create_researcher_agent
from discount_analyst.agents.researcher.user_prompt import (
    create_user_prompt as create_researcher_user_prompt,
)
from discount_analyst.agents.strategist.strategist import create_strategist_agent
from discount_analyst.agents.strategist.user_prompt import (
    create_user_prompt as create_strategist_user_prompt,
)
from discount_analyst.agents.profiler.profiler import create_profiler_agent
from discount_analyst.agents.profiler.user_prompt import create_profiler_user_prompt
from discount_analyst.agents.surveyor.surveyor import create_surveyor_agent
from discount_analyst.agents.surveyor.user_prompt import USER_PROMPT
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.agents.appraiser.schema import AppraiserInput
from discount_analyst.config.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.pipeline.builders import (
    build_sentinel_rejection,
    verdict_from_decision,
)
from discount_analyst.pipeline.schema import SentinelRejection, Verdict
from scripts.agents.run_appraiser import (
    StockRunArgs,
    display_agent_output,
    run_agent,
    run_dcf_and_display,
    save_run_output,
)
from scripts.common.cli import (
    add_agent_cli_model_argument,
    add_agent_cli_web_search_arguments,
)
from scripts.common.artefacts import write_agent_json, write_verdicts_json
from scripts.common.run_outputs import (
    ArbiterRunOutput,
    ProfilerRunOutput,
    SentinelRunOutput,
    ResearcherRunOutput,
    StrategistRunOutput,
    SurveyorRunOutput,
    TurnUsage,
)
from scripts.common.usage import extract_turn_usage
from scripts.utils.setup_logfire import setup_logfire

setup_logfire()

console = Console()


@dataclass
class AgentRunResult:
    output: DeepResearchReport
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    turn_usage: list[TurnUsage]


@dataclass
class StrategistAgentRunResult:
    output: MispricingThesis
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    turn_usage: list[TurnUsage]


@dataclass
class SentinelAgentRunResult:
    output: EvaluationReport
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    turn_usage: list[TurnUsage]


@dataclass
class FailedCandidateRun:
    ticker: str
    candidate_index: int
    error: str


@dataclass
class FailedStrategistRun:
    ticker: str
    candidate_index: int
    error: str


@dataclass
class FailedSentinelRun:
    ticker: str
    candidate_index: int
    error: str


@dataclass
class FailedAppraiserRun:
    ticker: str
    candidate_index: int
    error: str


@dataclass
class FailedArbiterRun:
    ticker: str
    candidate_index: int
    error: str


@dataclass
class FailedProfilerRun:
    ticker: str
    candidate_index: int
    error: str


@dataclass
class ArbiterAgentRunResult:
    output: ArbiterDecision
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    turn_usage: list[TurnUsage]


class WorkflowArgs(BaseModel):
    model: ModelName
    use_perplexity: bool
    use_mcp_financial_data: bool
    risk_free_rate: float
    is_existing_position: bool
    profiler_tickers: list[str] | None = None


def parse_args() -> WorkflowArgs:
    parser = argparse.ArgumentParser(
        description=(
            "Run Surveyor once (default) or Profiler per ticker (--profiler-tickers), "
            "then Researcher sequentially for each candidate, "
            "then Strategist and Sentinel for each successful Researcher and Strategist run, "
            "then Appraiser and DCF when the Sentinel valuation gate passes, "
            "then Arbiter; writes Verdict rows and a verdicts JSON artefact."
        )
    )
    add_agent_cli_model_argument(parser)
    add_agent_cli_web_search_arguments(parser)
    parser.add_argument(
        "--risk-free-rate",
        type=float,
        required=True,
        help="Risk-free rate as a decimal for DCF (e.g. 0.045 for 4.5%%).",
    )
    parser.add_argument(
        "--is-existing-position",
        action="store_true",
        help=(
            "Treat each candidate as an existing portfolio holding for programmatic "
            "rejections and Arbiter recommended_action framing."
        ),
    )
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help=(
            "Do not register EODHD/FMP MCP toolsets (required for Google models; "
            "optional for Anthropic/OpenAI)."
        ),
    )
    parser.add_argument(
        "--profiler-tickers",
        nargs="+",
        metavar="TICKER",
        default=None,
        help=(
            "When set, skip Surveyor and run Profiler once per ticker; "
            "each run produces one pipeline candidate."
        ),
    )
    raw = parser.parse_args()
    if not (0 < raw.risk_free_rate <= 0.15):
        parser.error(
            f"--risk-free-rate must be a decimal between 0 and 0.15 (e.g. 0.045 for 4.5%). "
            f"Got {raw.risk_free_rate}."
        )
    profiler_tickers = (
        [t.strip() for t in raw.profiler_tickers if t.strip()]
        if raw.profiler_tickers is not None
        else None
    )
    return WorkflowArgs(
        model=raw.model,
        use_perplexity=raw.use_perplexity,
        use_mcp_financial_data=not raw.no_mcp,
        risk_free_rate=raw.risk_free_rate,
        is_existing_position=raw.is_existing_position,
        profiler_tickers=profiler_tickers,
    )


def _build_researcher_suffixes(
    candidates: list[SurveyorCandidate],
) -> list[str]:
    ticker_counts = Counter(candidate.ticker.casefold() for candidate in candidates)
    ticker_seen: Counter[str] = Counter()
    suffixes: list[str] = []

    for candidate in candidates:
        folded = candidate.ticker.casefold()
        ticker_seen[folded] += 1
        if ticker_counts[folded] > 1:
            suffixes.append(f"{candidate.ticker.upper()}-{ticker_seen[folded]}")
        else:
            suffixes.append(candidate.ticker.upper())
    return suffixes


def display_candidate_table(
    candidates: list[SurveyorCandidate],
    *,
    title: str,
) -> None:
    table = Table(
        title=title,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Exchange", style="yellow")
    table.add_column("Market Cap", style="blue", justify="right")
    for candidate in candidates:
        table.add_row(
            candidate.ticker,
            candidate.company_name,
            candidate.exchange.value,
            candidate.market_cap_display,
        )
    console.print(table)


def display_researcher_output(output: DeepResearchReport) -> None:
    candidate = output.candidate
    table = Table(title=f"Researcher - {candidate.ticker}", show_header=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Company", candidate.company_name)
    table.add_row("Narrative", output.market_narrative.dominant_narrative)
    table.add_row(
        "Open gaps",
        str(len(output.data_gaps_update.remaining_open_gaps)),
    )
    table.add_row(
        "Material gaps",
        str(len(output.data_gaps_update.material_open_gaps)),
    )
    console.print(table)


def display_strategist_output(output: MispricingThesis) -> None:
    table = Table(title=f"Strategist - {output.ticker}", show_header=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Company", output.company_name)
    table.add_row("Mispricing type", output.mispricing_type)
    table.add_row("Conviction", output.conviction_level)
    console.print(table)


def display_sentinel_output(output: EvaluationReport) -> None:
    table = Table(title=f"Sentinel - {output.ticker}", show_header=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Company", output.company_name)
    table.add_row("Thesis verdict", output.thesis_verdict)
    table.add_row(
        "Valuation gate (derived)",
        (
            "Proceed to valuation"
            if sentinel_proceeds_to_valuation(output)
            else "Do not proceed"
        ),
    )
    console.print(table)


def display_failure_summary(failures: list[FailedCandidateRun]) -> None:
    table = Table(
        title="Researcher Failures",
        show_header=True,
        header_style="bold red",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Candidate Index", style="yellow")
    table.add_column("Error", style="white")
    for failed in failures:
        table.add_row(failed.ticker, str(failed.candidate_index), failed.error)
    console.print(table)


def display_strategist_failure_summary(failures: list[FailedStrategistRun]) -> None:
    table = Table(
        title="Strategist Failures",
        show_header=True,
        header_style="bold red",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Candidate Index", style="yellow")
    table.add_column("Error", style="white")
    for failed in failures:
        table.add_row(failed.ticker, str(failed.candidate_index), failed.error)
    console.print(table)


def display_sentinel_failure_summary(failures: list[FailedSentinelRun]) -> None:
    table = Table(
        title="Sentinel Failures",
        show_header=True,
        header_style="bold red",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Candidate Index", style="yellow")
    table.add_column("Error", style="white")
    for failed in failures:
        table.add_row(failed.ticker, str(failed.candidate_index), failed.error)
    console.print(table)


def display_appraiser_failure_summary(failures: list[FailedAppraiserRun]) -> None:
    table = Table(
        title="Appraiser Failures",
        show_header=True,
        header_style="bold red",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Candidate Index", style="yellow")
    table.add_column("Error", style="white")
    for failed in failures:
        table.add_row(failed.ticker, str(failed.candidate_index), failed.error)
    console.print(table)


def display_arbiter_failure_summary(failures: list[FailedArbiterRun]) -> None:
    table = Table(
        title="Arbiter Failures",
        show_header=True,
        header_style="bold red",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Candidate Index", style="yellow")
    table.add_column("Error", style="white")
    for failed in failures:
        table.add_row(failed.ticker, str(failed.candidate_index), failed.error)
    console.print(table)


def display_profiler_failure_summary(failures: list[FailedProfilerRun]) -> None:
    table = Table(
        title="Profiler Failures",
        show_header=True,
        header_style="bold red",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Request Index", style="yellow")
    table.add_column("Error", style="white")
    for failed in failures:
        table.add_row(failed.ticker, str(failed.candidate_index), failed.error)
    console.print(table)


def display_verdicts_table(verdicts: list[Verdict]) -> None:
    """Portfolio-style summary: one row per Verdict."""
    if not verdicts:
        return
    table = Table(
        title="Verdicts summary",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Company", style="green")
    table.add_column("Rating", style="yellow")
    table.add_column("Recommended action", style="white")
    table.add_column("Provenance", style="blue")
    table.add_column("Existing", justify="center")
    table.add_column("Rejection reason", style="dim")
    table.add_column("Conviction", style="white")
    table.add_column("MoS verdict", style="white")
    for v in verdicts:
        prov = "Arbiter" if isinstance(v.decision, ArbiterDecision) else "Sentinel"
        if isinstance(v.decision, SentinelRejection):
            rej = v.decision.rejection_reason
            conv = "—"
            mos = "—"
        else:
            rej = "—"
            conv = v.decision.conviction
            mos = v.decision.margin_of_safety.margin_of_safety_verdict
        table.add_row(
            v.ticker,
            v.company_name,
            v.rating,
            v.recommended_action,
            prov,
            "Y" if v.is_existing_position else "N",
            rej,
            conv,
            mos,
        )
    console.print(table)


async def run_arbiter_once(
    *,
    model_name: ModelName,
    arbiter_input: ArbiterInput,
) -> ArbiterAgentRunResult:
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_arbiter_agent(ai_models_config)
    user_prompt = create_arbiter_user_prompt(arbiter_input=arbiter_input)
    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
    )
    output = outcome.output
    usage = outcome.usage
    turn_usage = extract_turn_usage(outcome.all_messages)
    elapsed_s = outcome.elapsed_s
    console.log(f"Arbiter completed for {arbiter_input.stock_candidate.ticker}.")
    return ArbiterAgentRunResult(
        output=output,
        elapsed_s=elapsed_s,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_write_tokens=getattr(usage, "cache_write_tokens", 0),
        cache_read_tokens=getattr(usage, "cache_read_tokens", 0),
        tool_calls=getattr(usage, "tool_calls", 0),
        turn_usage=turn_usage,
    )


def save_arbiter_output(
    *,
    model_name: ModelName,
    ticker: str,
    risk_free_rate: float,
    is_existing_position: bool,
    run_result: ArbiterAgentRunResult,
    source_surveyor_report: str,
    source_candidate_index: int,
    source_researcher_report: str,
    source_strategist_report: str,
    source_sentinel_report: str,
    source_appraiser_report: str,
    filename_suffix: str,
) -> str:
    run_output = ArbiterRunOutput(
        ticker=ticker,
        model_name=model_name.value,
        risk_free_rate=risk_free_rate,
        is_existing_position=is_existing_position,
        source_surveyor_report=source_surveyor_report,
        source_candidate_index=source_candidate_index,
        source_researcher_report=source_researcher_report,
        source_strategist_report=source_strategist_report,
        source_sentinel_report=source_sentinel_report,
        source_appraiser_report=source_appraiser_report,
        elapsed_s=run_result.elapsed_s,
        input_tokens=run_result.input_tokens,
        output_tokens=run_result.output_tokens,
        cache_write_tokens=run_result.cache_write_tokens,
        cache_read_tokens=run_result.cache_read_tokens,
        tool_calls=run_result.tool_calls,
        turn_usage=run_result.turn_usage,
        output=run_result.output,
    )
    out_path = write_agent_json(
        payload=run_output,
        model_name=model_name,
        agent_name=AgentName.ARBITER,
        filename_suffix=filename_suffix,
    )
    return str(out_path)


async def run_profiler_once(
    *,
    model_name: ModelName,
    ticker: str,
    use_perplexity: bool,
    use_mcp_financial_data: bool,
    filename_suffix: str,
) -> tuple[ProfilerRunOutput, str]:
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_profiler_agent(
        ai_models_config=ai_models_config,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
    )
    user_prompt = create_profiler_user_prompt(ticker)
    console.log(f"Running Profiler agent for {ticker!r} (model: {model_name})...")
    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
    )
    output = outcome.output
    usage = outcome.usage
    turn_usage = extract_turn_usage(outcome.all_messages)
    elapsed_s = outcome.elapsed_s
    run_output = ProfilerRunOutput(
        model_name=model_name.value,
        elapsed_s=elapsed_s,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        turn_usage=turn_usage,
        output=output,
        ticker=ticker,
    )
    out_path = write_agent_json(
        payload=run_output,
        model_name=model_name,
        agent_name=AgentName.PROFILER,
        filename_suffix=filename_suffix,
    )
    console.log(f"Profiler completed for {ticker!r}; saved to {out_path}.")
    return run_output, str(out_path)


async def run_surveyor_once(
    *,
    model_name: ModelName,
    use_perplexity: bool,
    use_mcp_financial_data: bool,
) -> tuple[SurveyorRunOutput, str]:
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_surveyor_agent(
        ai_models_config=ai_models_config,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
    )
    console.log(f"Running Surveyor agent (model: {model_name})...")

    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=USER_PROMPT,
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
    )
    output = outcome.output
    usage = outcome.usage
    turn_usage = extract_turn_usage(outcome.all_messages)
    elapsed_s = outcome.elapsed_s
    run_output = SurveyorRunOutput(
        model_name=model_name.value,
        elapsed_s=elapsed_s,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        turn_usage=turn_usage,
        output=output,
    )
    out_path = write_agent_json(
        payload=run_output,
        model_name=model_name,
        agent_name=AgentName.SURVEYOR,
    )
    return run_output, str(out_path)


async def run_researcher_once(
    *,
    model_name: ModelName,
    surveyor_report_path: str,
    candidate_index: int,
    candidate: SurveyorCandidate,
    use_perplexity: bool,
    use_mcp_financial_data: bool,
) -> AgentRunResult:
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_researcher_agent(
        ai_models_config,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
    )
    user_prompt = create_researcher_user_prompt(surveyor_candidate=candidate)

    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
    )
    output = outcome.output
    usage = outcome.usage
    turn_usage = extract_turn_usage(outcome.all_messages)
    elapsed_s = outcome.elapsed_s
    console.log(
        f"Researcher completed for {candidate.ticker} "
        f"(candidate_index={candidate_index}, source={surveyor_report_path})."
    )
    return AgentRunResult(
        output=output,
        elapsed_s=elapsed_s,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_write_tokens=getattr(usage, "cache_write_tokens", 0),
        cache_read_tokens=getattr(usage, "cache_read_tokens", 0),
        tool_calls=getattr(usage, "tool_calls", 0),
        turn_usage=turn_usage,
    )


async def run_strategist_once(
    *,
    model_name: ModelName,
    surveyor_candidate: SurveyorCandidate,
    deep_research: DeepResearchReport,
) -> StrategistAgentRunResult:
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_strategist_agent(ai_models_config)
    user_prompt = create_strategist_user_prompt(
        surveyor_candidate=surveyor_candidate,
        deep_research=deep_research,
    )

    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
    )
    output = outcome.output
    usage = outcome.usage
    turn_usage = extract_turn_usage(outcome.all_messages)
    elapsed_s = outcome.elapsed_s
    console.log(f"Strategist completed for {surveyor_candidate.ticker}.")
    return StrategistAgentRunResult(
        output=output,
        elapsed_s=elapsed_s,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_write_tokens=getattr(usage, "cache_write_tokens", 0),
        cache_read_tokens=getattr(usage, "cache_read_tokens", 0),
        tool_calls=getattr(usage, "tool_calls", 0),
        turn_usage=turn_usage,
    )


async def run_sentinel_once(
    *,
    model_name: ModelName,
    surveyor_candidate: SurveyorCandidate,
    deep_research: DeepResearchReport,
    thesis: MispricingThesis,
) -> SentinelAgentRunResult:
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_sentinel_agent(ai_models_config)
    user_prompt = create_sentinel_user_prompt(
        surveyor_candidate=surveyor_candidate,
        deep_research=deep_research,
        thesis=thesis,
    )

    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
    )
    output = outcome.output
    usage = outcome.usage
    turn_usage = extract_turn_usage(outcome.all_messages)
    elapsed_s = outcome.elapsed_s
    console.log(f"Sentinel completed for {surveyor_candidate.ticker}.")
    return SentinelAgentRunResult(
        output=output,
        elapsed_s=elapsed_s,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_write_tokens=getattr(usage, "cache_write_tokens", 0),
        cache_read_tokens=getattr(usage, "cache_read_tokens", 0),
        tool_calls=getattr(usage, "tool_calls", 0),
        turn_usage=turn_usage,
    )


def save_researcher_output(
    *,
    model_name: ModelName,
    surveyor_report_path: str,
    candidate_index: int,
    candidate: SurveyorCandidate,
    run_result: AgentRunResult,
    filename_suffix: str,
) -> str:
    run_output = ResearcherRunOutput(
        ticker=candidate.ticker,
        model_name=model_name.value,
        source_surveyor_report=surveyor_report_path,
        source_candidate_index=candidate_index,
        elapsed_s=run_result.elapsed_s,
        input_tokens=run_result.input_tokens,
        output_tokens=run_result.output_tokens,
        cache_write_tokens=run_result.cache_write_tokens,
        cache_read_tokens=run_result.cache_read_tokens,
        tool_calls=run_result.tool_calls,
        turn_usage=run_result.turn_usage,
        output=run_result.output,
    )
    out_path = write_agent_json(
        payload=run_output,
        model_name=model_name,
        agent_name=AgentName.RESEARCHER,
        filename_suffix=filename_suffix,
    )
    return str(out_path)


def save_strategist_output(
    *,
    model_name: ModelName,
    source_surveyor_report: str,
    source_candidate_index: int,
    source_researcher_report: str,
    ticker: str,
    run_result: StrategistAgentRunResult,
    filename_suffix: str,
) -> str:
    run_output = StrategistRunOutput(
        ticker=ticker,
        model_name=model_name.value,
        source_surveyor_report=source_surveyor_report,
        source_candidate_index=source_candidate_index,
        source_researcher_report=source_researcher_report,
        elapsed_s=run_result.elapsed_s,
        input_tokens=run_result.input_tokens,
        output_tokens=run_result.output_tokens,
        cache_write_tokens=run_result.cache_write_tokens,
        cache_read_tokens=run_result.cache_read_tokens,
        tool_calls=run_result.tool_calls,
        turn_usage=run_result.turn_usage,
        output=run_result.output,
    )
    out_path = write_agent_json(
        payload=run_output,
        model_name=model_name,
        agent_name=AgentName.STRATEGIST,
        filename_suffix=filename_suffix,
    )
    return str(out_path)


def save_sentinel_output(
    *,
    model_name: ModelName,
    source_surveyor_report: str,
    source_candidate_index: int,
    source_researcher_report: str,
    source_strategist_report: str,
    ticker: str,
    run_result: SentinelAgentRunResult,
    filename_suffix: str,
) -> str:
    run_output = SentinelRunOutput(
        ticker=ticker,
        model_name=model_name.value,
        source_surveyor_report=source_surveyor_report,
        source_candidate_index=source_candidate_index,
        source_researcher_report=source_researcher_report,
        source_strategist_report=source_strategist_report,
        elapsed_s=run_result.elapsed_s,
        input_tokens=run_result.input_tokens,
        output_tokens=run_result.output_tokens,
        cache_write_tokens=run_result.cache_write_tokens,
        cache_read_tokens=run_result.cache_read_tokens,
        tool_calls=run_result.tool_calls,
        turn_usage=run_result.turn_usage,
        output=run_result.output,
    )
    out_path = write_agent_json(
        payload=run_output,
        model_name=model_name,
        agent_name=AgentName.SENTINEL,
        filename_suffix=filename_suffix,
    )
    return str(out_path)


async def _run_appraiser_dcf_arbiter_for_candidate(
    *,
    args: WorkflowArgs,
    candidate: SurveyorCandidate,
    index: int,
    source_entry_report_path: str,
    researcher_out_path: str,
    strat_path: str,
    sentinel_path: str,
    filename_suffix: str,
    run_result: AgentRunResult,
    strat_result: StrategistAgentRunResult,
    sent_result: SentinelAgentRunResult,
    verdicts: list[Verdict],
    arbiter_failures: list[FailedArbiterRun],
) -> None:
    appraiser_input = AppraiserInput(
        stock_candidate=candidate,
        deep_research=run_result.output,
        thesis=strat_result.output,
        evaluation=sent_result.output,
        risk_free_rate=args.risk_free_rate,
    )
    stock_args = StockRunArgs(
        surveyor_candidate=candidate,
        risk_free_rate=args.risk_free_rate,
        model=args.model,
    )
    agent_result = await run_agent(
        stock_args,
        appraiser_input,
        use_perplexity=args.use_perplexity,
        use_mcp_financial_data=args.use_mcp_financial_data,
    )
    display_agent_output(agent_result.output)
    dcf_result, dcf_error = run_dcf_and_display(stock_args, agent_result.output)
    appraiser_out_path = save_run_output(
        stock_args,
        agent_result.output,
        agent_result,
        dcf_result,
        dcf_error,
        source_surveyor_report=source_entry_report_path,
        source_candidate_index=index,
        source_researcher_report=researcher_out_path,
        source_strategist_report=strat_path,
        source_sentinel_report=sentinel_path,
        filename_suffix=filename_suffix,
    )
    console.print(f"Saved Appraiser output: [dim]{appraiser_out_path}[/dim]")

    if dcf_result is None:
        console.print(
            f"[yellow]Warning: DCF did not produce a result for "
            f"{candidate.ticker}; skipping Arbiter and omitting a "
            "Verdict for this candidate.[/yellow]"
        )
        if dcf_error:
            console.print(f"[dim]{dcf_error}[/dim]")
        return

    valuation = ValuationResult(
        appraiser_output=agent_result.output,
        dcf_result=dcf_result,
    )
    arbiter_input = ArbiterInput(
        stock_candidate=candidate,
        deep_research=run_result.output,
        thesis=strat_result.output,
        evaluation=sent_result.output,
        valuation=valuation,
        risk_free_rate=args.risk_free_rate,
        is_existing_position=args.is_existing_position,
    )
    try:
        arb_run = await run_arbiter_once(
            model_name=args.model,
            arbiter_input=arbiter_input,
        )
        arb_decision = arb_run.output.model_copy(
            update={"decision_date": date.today().isoformat()}
        )
        verdicts.append(verdict_from_decision(arb_decision))
        arb_run_saved = replace(arb_run, output=arb_decision)
        arb_path = save_arbiter_output(
            model_name=args.model,
            ticker=candidate.ticker,
            risk_free_rate=args.risk_free_rate,
            is_existing_position=args.is_existing_position,
            run_result=arb_run_saved,
            source_surveyor_report=source_entry_report_path,
            source_candidate_index=index,
            source_researcher_report=researcher_out_path,
            source_strategist_report=strat_path,
            source_sentinel_report=sentinel_path,
            source_appraiser_report=str(appraiser_out_path),
            filename_suffix=filename_suffix,
        )
        console.print(f"Saved Arbiter output: [dim]{arb_path}[/dim]")
    except Exception as arb_exc:
        arbiter_failures.append(
            FailedArbiterRun(
                ticker=candidate.ticker,
                candidate_index=index,
                error=str(arb_exc),
            )
        )
        console.print(
            f"[red]Arbiter failed for {candidate.ticker} "
            f"(candidate_index={index}). Continuing...[/red]"
        )
        console.print(f"[dim]{arb_exc}[/dim]")


async def main() -> None:
    args = parse_args()
    profiler_failures: list[FailedProfilerRun] = []

    if args.profiler_tickers:
        if args.is_existing_position:
            console.log(
                "[yellow]Profiler mode: --is-existing-position is not passed into "
                "Profiler prompts; it still affects Arbiter and programmatic gates.[/yellow]"
            )
        candidates: list[SurveyorCandidate] = []
        entry_report_paths: list[str] = []
        for req_index, raw_ticker in enumerate(args.profiler_tickers):
            try:
                profiler_run, profiler_path = await run_profiler_once(
                    model_name=args.model,
                    ticker=raw_ticker,
                    use_perplexity=args.use_perplexity,
                    use_mcp_financial_data=args.use_mcp_financial_data,
                    filename_suffix=raw_ticker,
                )
            except Exception as exc:
                profiler_failures.append(
                    FailedProfilerRun(
                        ticker=raw_ticker,
                        candidate_index=req_index,
                        error=str(exc),
                    )
                )
                console.print(
                    f"[red]Profiler failed for {raw_ticker!r} "
                    f"(request_index={req_index}). Continuing...[/red]"
                )
                console.print(f"[dim]{exc}[/dim]")
                continue
            candidates.append(profiler_run.output.candidate)
            entry_report_paths.append(profiler_path)

        display_candidate_table(
            candidates,
            title="Profiler candidates",
        )
        console.print()
        entry_mode = "Profiler"
    else:
        surveyor_run_output, surveyor_path = await run_surveyor_once(
            model_name=args.model,
            use_perplexity=args.use_perplexity,
            use_mcp_financial_data=args.use_mcp_financial_data,
        )
        candidates = surveyor_run_output.output.candidates
        display_candidate_table(
            surveyor_run_output.output.candidates,
            title="Surveyor candidates",
        )
        console.print(f"\nSaved Surveyor output: [dim]{surveyor_path}[/dim]\n")
        entry_report_paths = [surveyor_path] * len(candidates)
        entry_mode = "Surveyor"

    console.log(
        f"Starting sequential Researcher runs for {len(candidates)} candidates..."
    )

    suffixes = _build_researcher_suffixes(candidates)
    failures: list[FailedCandidateRun] = []
    strategist_failures: list[FailedStrategistRun] = []
    sentinel_failures: list[FailedSentinelRun] = []
    appraiser_failures: list[FailedAppraiserRun] = []
    arbiter_failures: list[FailedArbiterRun] = []
    verdicts: list[Verdict] = []
    researcher_successes = 0
    strategist_successes = 0
    sentinel_successes = 0
    appraiser_successes = 0
    appraiser_skipped_sentinel = 0

    for index, candidate in enumerate(candidates):
        if index > 0:
            console.print("\n[bold]--- Next candidate ---[/bold]\n")
        if suffixes[index] != candidate.ticker.upper():
            console.print(
                f"[yellow]Duplicate ticker '{candidate.ticker}' detected; "
                f"using output suffix '{suffixes[index]}'.[/yellow]"
            )

        entry_path = entry_report_paths[index]
        try:
            run_result = await run_researcher_once(
                model_name=args.model,
                surveyor_report_path=entry_path,
                candidate_index=index,
                candidate=candidate,
                use_perplexity=args.use_perplexity,
                use_mcp_financial_data=args.use_mcp_financial_data,
            )
        except Exception as exc:
            failures.append(
                FailedCandidateRun(
                    ticker=candidate.ticker,
                    candidate_index=index,
                    error=str(exc),
                )
            )
            console.print(
                f"[red]Researcher failed for {candidate.ticker} "
                f"(candidate_index={index}). Continuing...[/red]"
            )
            console.print(f"[dim]{exc}[/dim]")
            continue

        display_researcher_output(run_result.output)
        researcher_out_path = save_researcher_output(
            model_name=args.model,
            surveyor_report_path=entry_path,
            candidate_index=index,
            candidate=candidate,
            run_result=run_result,
            filename_suffix=suffixes[index],
        )
        researcher_successes += 1
        console.print(f"Saved Researcher output: [dim]{researcher_out_path}[/dim]")

        try:
            strat_result = await run_strategist_once(
                model_name=args.model,
                surveyor_candidate=candidate,
                deep_research=run_result.output,
            )
        except Exception as exc:
            strategist_failures.append(
                FailedStrategistRun(
                    ticker=candidate.ticker,
                    candidate_index=index,
                    error=str(exc),
                )
            )
            console.print(
                f"[red]Strategist failed for {candidate.ticker} "
                f"(candidate_index={index}). Continuing...[/red]"
            )
            console.print(f"[dim]{exc}[/dim]")
            continue

        display_strategist_output(strat_result.output)
        strat_path = save_strategist_output(
            model_name=args.model,
            source_surveyor_report=entry_path,
            source_candidate_index=index,
            source_researcher_report=researcher_out_path,
            ticker=candidate.ticker,
            run_result=strat_result,
            filename_suffix=suffixes[index],
        )
        strategist_successes += 1
        console.print(f"Saved Strategist output: [dim]{strat_path}[/dim]")

        try:
            sent_result = await run_sentinel_once(
                model_name=args.model,
                surveyor_candidate=candidate,
                deep_research=run_result.output,
                thesis=strat_result.output,
            )
        except Exception as exc:
            sentinel_failures.append(
                FailedSentinelRun(
                    ticker=candidate.ticker,
                    candidate_index=index,
                    error=str(exc),
                )
            )
            console.print(
                f"[red]Sentinel failed for {candidate.ticker} "
                f"(candidate_index={index}). Continuing...[/red]"
            )
            console.print(f"[dim]{exc}[/dim]")
            continue

        display_sentinel_output(sent_result.output)
        sentinel_path = save_sentinel_output(
            model_name=args.model,
            source_surveyor_report=entry_path,
            source_candidate_index=index,
            source_researcher_report=researcher_out_path,
            source_strategist_report=strat_path,
            ticker=candidate.ticker,
            run_result=sent_result,
            filename_suffix=suffixes[index],
        )
        sentinel_successes += 1
        console.print(f"Saved Sentinel output: [dim]{sentinel_path}[/dim]")

        if not sentinel_proceeds_to_valuation(sent_result.output):
            appraiser_skipped_sentinel += 1
            decision_day = date.today().isoformat()
            rejection = build_sentinel_rejection(
                sent_result.output,
                strat_result.output,
                is_existing_position=args.is_existing_position,
                decision_date=decision_day,
            )
            verdicts.append(verdict_from_decision(rejection))
            console.log(
                f"Skipping Appraiser for {candidate.ticker}: "
                "valuation gate is Do not proceed "
                f"(thesis_verdict={sent_result.output.thesis_verdict!r}, "
                "overall_red_flag_verdict="
                f"{sent_result.output.red_flag_screen.overall_red_flag_verdict!r})."
            )
            continue

        console.log(
            f"Sentinel valuation gate passed; "
            f"running Appraiser + DCF for {candidate.ticker}..."
        )
        try:
            await _run_appraiser_dcf_arbiter_for_candidate(
                args=args,
                candidate=candidate,
                index=index,
                source_entry_report_path=entry_path,
                researcher_out_path=researcher_out_path,
                strat_path=strat_path,
                sentinel_path=sentinel_path,
                filename_suffix=suffixes[index],
                run_result=run_result,
                strat_result=strat_result,
                sent_result=sent_result,
                verdicts=verdicts,
                arbiter_failures=arbiter_failures,
            )
            appraiser_successes += 1
        except Exception as appr_exc:
            appraiser_failures.append(
                FailedAppraiserRun(
                    ticker=candidate.ticker,
                    candidate_index=index,
                    error=str(appr_exc),
                )
            )
            console.print(
                f"[red]Appraiser failed for {candidate.ticker} "
                f"(candidate_index={index}). Continuing...[/red]"
            )
            console.print(f"[dim]{appr_exc}[/dim]")
            continue

    if verdicts:
        verdicts_path = write_verdicts_json(verdicts=verdicts, model_name=args.model)
        console.print(f"\nSaved verdicts JSON: [dim]{verdicts_path}[/dim]\n")
        display_verdicts_table(verdicts)

    summary_lines = [
        f"Workflow complete: {entry_mode} entry through Arbiter (gated)",
        f"Candidates: {len(candidates)}",
    ]
    if args.profiler_tickers is not None:
        summary_lines.append(f"Profiler failures: {len(profiler_failures)}")
    summary_lines.extend(
        [
            f"Researcher successes: {researcher_successes}",
            f"Researcher failures: {len(failures)}",
            f"Strategist successes: {strategist_successes}",
            f"Strategist failures: {len(strategist_failures)}",
            f"Sentinel successes: {sentinel_successes}",
            f"Sentinel failures: {len(sentinel_failures)}",
            f"Appraiser successes: {appraiser_successes}",
            f"Appraiser failures: {len(appraiser_failures)}",
            f"Appraiser skipped (valuation gate): {appraiser_skipped_sentinel}",
            f"Verdicts recorded: {len(verdicts)}",
            f"Arbiter failures: {len(arbiter_failures)}",
        ]
    )
    console.print(Panel.fit("\n".join(summary_lines), border_style="cyan"))
    if profiler_failures:
        display_profiler_failure_summary(profiler_failures)
    if failures:
        display_failure_summary(failures)
    if strategist_failures:
        display_strategist_failure_summary(strategist_failures)
    if sentinel_failures:
        display_sentinel_failure_summary(sentinel_failures)
    if appraiser_failures:
        display_appraiser_failure_summary(appraiser_failures)
    if arbiter_failures:
        display_arbiter_failure_summary(arbiter_failures)


if __name__ == "__main__":
    asyncio.run(main())
