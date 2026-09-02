"""Run Surveyor or Profiler entry, then Researcher through Sentinel, gated Appraiser, deterministic rating, Verdicts."""

import argparse
import asyncio
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel

from discount_analyst.agents.sentinel.schema import (
    EvaluationReport,
    sentinel_proceeds_to_valuation,
)
from discount_analyst.agents.sentinel.sentinel import create_sentinel_agent
from discount_analyst.agents.sentinel.derive_thesis_verdict import (
    finalise_sentinel_evaluation,
)
from discount_analyst.agents.sentinel.user_prompt import (
    create_user_prompt as create_sentinel_user_prompt,
)
from discount_analyst.agents.runtime.agent_names import AgentName
from discount_analyst.agents.runtime.streamed_agent_run import run_streamed_agent
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
from discount_analyst.agents.strategist.schema import (
    MispricingThesis,
    StrategistDecision,
)
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.application.theses import resolve_live_thesis
from discount_analyst.config.ai_models_config import AIModelsConfig
from discount_analyst.config.settings import settings as app_settings
from discount_analyst.domain.model_selection.model_name import ModelName
from discount_analyst.application.allocations.assemble import (
    CompletedLaneBundle,
    completed_lane_bundle_from_verdict,
)
from discount_analyst.application.allocations.errors import AllocationAssemblyError
from discount_analyst.application.decisions.builders import (
    build_sentinel_rejection,
    verdict_from_decision,
)
from discount_analyst.domain.allocations.invariants import AllocationInvariantError
from discount_analyst.domain.decisions.schema import (
    Verdict,
)
from discount_analyst.agents.runtime.terminal_run import (
    TerminalRunOptions,
    terminal_run_options,
)
from discount_analyst.entrypoints.cli.shared.cli import (
    add_agent_cli_web_search_arguments,
    add_agent_terminal_argument,
    terminal_run_options_for_cli,
)
from discount_analyst.entrypoints.cli.shared.artefacts import (
    write_agent_json,
    write_verdicts_json,
)
from discount_analyst.entrypoints.cli.shared.run_outputs import (
    ProfilerRunOutput,
    SentinelRunOutput,
    ResearcherRunOutput,
    StrategistRunOutput,
    SurveyorRunOutput,
    TurnUsage,
)
from discount_analyst.entrypoints.cli.shared.usage import extract_turn_usage
from discount_analyst.entrypoints.cli.workflows.cli_curator import (
    load_cli_portfolio_snapshot,
    run_cli_curator,
)
from discount_analyst.entrypoints.cli.workflows.cli_appraiser_lane import (
    run_cli_appraiser_lane,
)
from discount_analyst.entrypoints.cli.workflows.workflow_display import (
    FailedAppraiserRun,
    FailedCandidateRun,
    FailedProfilerRun,
    FailedSentinelRun,
    FailedStrategistRun,
    display_appraiser_failure_summary,
    display_candidate_table,
    display_failure_summary,
    display_profiler_failure_summary,
    display_researcher_output,
    display_sentinel_failure_summary,
    display_sentinel_output,
    display_strategist_failure_summary,
    display_strategist_output,
    display_verdicts_table,
)
from discount_analyst.adapters.observability.script_setup import setup_logfire

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
    decision: StrategistDecision
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


class WorkflowArgs(BaseModel):
    use_perplexity: bool
    use_mcp_financial_data: bool
    use_terminal: bool
    risk_free_rate_pct: float
    is_existing_position: bool
    profiler_tickers: list[str] | None = None
    snapshot: Path


def parse_args() -> WorkflowArgs:
    parser = argparse.ArgumentParser(
        description=(
            "Run Surveyor once (default) or Profiler per ticker (--profiler-tickers), "
            "then Researcher sequentially for each candidate, "
            "then Strategist and Sentinel for each successful Researcher and Strategist run, "
            "then Appraiser when the Sentinel valuation gate passes, "
            "then deterministic rating and a workflow-level Curator; "
            "writes Verdict rows, a verdicts JSON artefact, and a PortfolioAllocation artefact."
        )
    )
    add_agent_cli_web_search_arguments(parser)
    parser.add_argument(
        "--risk-free-rate",
        type=float,
        required=True,
        dest="risk_free_rate_pct",
        help=(
            "Risk-free rate as a percentage for valuation helpers "
            "(e.g. 4.5 means 4.5%%)."
        ),
    )
    parser.add_argument(
        "--is-existing-position",
        action="store_true",
        help=(
            "Treat each candidate as an existing portfolio holding for programmatic "
            "rejections and recommended_action framing."
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
    add_agent_terminal_argument(parser)
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
    parser.add_argument(
        "--snapshot",
        type=Path,
        required=True,
        help=(
            "JSON file containing a CurrentPortfolioSnapshot. Required; "
            "allocation is not run without a real position snapshot."
        ),
    )
    raw = parser.parse_args()
    if not (1 <= raw.risk_free_rate_pct <= 15):
        parser.error(
            f"--risk-free-rate must be a percentage between 1 and 15 (e.g. 4.5 for 4.5%). "
            f"Got {raw.risk_free_rate_pct}."
        )
    profiler_tickers = (
        [t.strip() for t in raw.profiler_tickers if t.strip()]
        if raw.profiler_tickers is not None
        else None
    )
    return WorkflowArgs(
        use_perplexity=raw.use_perplexity,
        use_mcp_financial_data=not raw.no_mcp,
        use_terminal=not raw.no_terminal,
        risk_free_rate_pct=raw.risk_free_rate_pct,
        is_existing_position=raw.is_existing_position,
        profiler_tickers=profiler_tickers,
        snapshot=raw.snapshot,
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


async def run_profiler_once(
    *,
    model_name: ModelName,
    ticker: str,
    use_perplexity: bool,
    use_mcp_financial_data: bool,
    terminal: TerminalRunOptions,
    filename_suffix: str,
) -> tuple[ProfilerRunOutput, str]:
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_profiler_agent(
        ai_models_config=ai_models_config,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
        terminal=terminal,
    )
    user_prompt = create_profiler_user_prompt(ticker)
    console.log(f"Running Profiler agent for {ticker!r} (model: {model_name})...")
    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
        terminal=terminal,
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
    terminal: TerminalRunOptions,
) -> tuple[SurveyorRunOutput, str]:
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_surveyor_agent(
        ai_models_config=ai_models_config,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
        terminal=terminal,
    )
    console.log(f"Running Surveyor agent (model: {model_name})...")

    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=USER_PROMPT,
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
        terminal=terminal,
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
    terminal: TerminalRunOptions,
) -> AgentRunResult:
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_researcher_agent(
        ai_models_config,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
        terminal=terminal,
    )
    user_prompt = create_researcher_user_prompt(
        lane_context=candidate.to_lane_context()
    )

    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
        terminal=terminal,
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
    use_perplexity: bool,
    use_mcp_financial_data: bool,
    terminal: TerminalRunOptions,
) -> StrategistAgentRunResult:
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_strategist_agent(
        ai_models_config,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
        terminal=terminal,
    )
    user_prompt = create_strategist_user_prompt(
        lane_context=surveyor_candidate.to_lane_context(),
        deep_research=deep_research,
        prior_thesis=None,
    )

    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
        terminal=terminal,
    )
    decision = outcome.output
    output = resolve_live_thesis(decision, None)
    usage = outcome.usage
    turn_usage = extract_turn_usage(outcome.all_messages)
    elapsed_s = outcome.elapsed_s
    console.log(f"Strategist completed for {surveyor_candidate.ticker}.")
    return StrategistAgentRunResult(
        decision=decision,
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
    is_existing_position: bool,
) -> SentinelAgentRunResult:
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_sentinel_agent(ai_models_config)
    user_prompt = create_sentinel_user_prompt(
        lane_context=surveyor_candidate.to_lane_context(),
        deep_research=deep_research,
        thesis=thesis,
        is_existing_position=is_existing_position,
    )

    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
        terminal=terminal_run_options(app_settings, enabled=False),
        run_settings=app_settings,
    )
    output = finalise_sentinel_evaluation(outcome.output, thesis)
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
        output=run_result.decision,
        live_thesis=run_result.output,
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


async def main() -> None:
    args = parse_args()
    defaults = app_settings.agent_default_models
    snapshot = load_cli_portfolio_snapshot(args.snapshot)
    terminal = terminal_run_options_for_cli(
        no_terminal=not args.use_terminal
    ).bind_session_id()
    profiler_failures: list[FailedProfilerRun] = []

    if args.profiler_tickers:
        if args.is_existing_position:
            console.log(
                "[yellow]Profiler mode: --is-existing-position is not passed into "
                "Profiler prompts; it still affects final rating framing and programmatic gates.[/yellow]"
            )
        candidates: list[SurveyorCandidate] = []
        entry_report_paths: list[str] = []
        for req_index, raw_ticker in enumerate(args.profiler_tickers):
            try:
                profiler_run, profiler_path = await run_profiler_once(
                    model_name=defaults.profiler,
                    ticker=raw_ticker,
                    use_perplexity=args.use_perplexity,
                    use_mcp_financial_data=args.use_mcp_financial_data,
                    terminal=terminal,
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
            model_name=defaults.surveyor,
            use_perplexity=args.use_perplexity,
            use_mcp_financial_data=args.use_mcp_financial_data,
            terminal=terminal,
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
    verdicts: list[Verdict] = []
    lane_bundles: list[CompletedLaneBundle] = []
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
                model_name=defaults.researcher,
                surveyor_report_path=entry_path,
                candidate_index=index,
                candidate=candidate,
                use_perplexity=args.use_perplexity,
                use_mcp_financial_data=args.use_mcp_financial_data,
                terminal=terminal,
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

        display_researcher_output(run_result.output, candidate=candidate)
        researcher_out_path = save_researcher_output(
            model_name=defaults.researcher,
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
                model_name=defaults.strategist,
                surveyor_candidate=candidate,
                deep_research=run_result.output,
                use_perplexity=args.use_perplexity,
                use_mcp_financial_data=args.use_mcp_financial_data,
                terminal=terminal,
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
            model_name=defaults.strategist,
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
                model_name=defaults.sentinel,
                surveyor_candidate=candidate,
                deep_research=run_result.output,
                thesis=strat_result.output,
                is_existing_position=args.is_existing_position,
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
            model_name=defaults.sentinel,
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
            rejection_verdict = verdict_from_decision(rejection)
            verdicts.append(rejection_verdict)
            lane_bundles.append(
                completed_lane_bundle_from_verdict(
                    source_run_id=f"cli-{suffixes[index]}",
                    verdict=rejection_verdict,
                    sector=candidate.sector,
                    industry=candidate.industry,
                    deep_research=run_result.output,
                    thesis=strat_result.output,
                    evaluation=sent_result.output,
                )
            )
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
            f"running Appraiser for {candidate.ticker}..."
        )
        try:
            verdict, appraiser_output = await run_cli_appraiser_lane(
                console=console,
                model=defaults.appraiser,
                risk_free_rate_pct=args.risk_free_rate_pct,
                use_perplexity=args.use_perplexity,
                use_mcp_financial_data=args.use_mcp_financial_data,
                is_existing_position=args.is_existing_position,
                terminal=terminal,
                candidate=candidate,
                index=index,
                source_entry_report_path=entry_path,
                researcher_out_path=researcher_out_path,
                strat_path=strat_path,
                sentinel_path=sentinel_path,
                filename_suffix=suffixes[index],
                deep_research=run_result.output,
                thesis=strat_result.output,
                evaluation=sent_result.output,
            )
            verdicts.append(verdict)
            lane_bundles.append(
                completed_lane_bundle_from_verdict(
                    source_run_id=f"cli-{suffixes[index]}",
                    verdict=verdict,
                    sector=candidate.sector,
                    industry=candidate.industry,
                    deep_research=run_result.output,
                    thesis=strat_result.output,
                    evaluation=sent_result.output,
                    appraiser_output=appraiser_output,
                )
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
        verdicts_path = write_verdicts_json(verdicts=verdicts)
        console.print(f"\nSaved verdicts JSON: [dim]{verdicts_path}[/dim]\n")
        display_verdicts_table(verdicts)

    if (
        profiler_failures
        or failures
        or strategist_failures
        or sentinel_failures
        or appraiser_failures
    ):
        console.print(
            "[yellow]Curator skipped because a lane failed or was cancelled.[/yellow]"
        )
    else:
        try:
            await run_cli_curator(
                console=console,
                model_name=defaults.curator,
                snapshot=snapshot,
                lane_bundles=tuple(lane_bundles),
            )
        except (AllocationAssemblyError, AllocationInvariantError) as exc:
            console.print(f"[red]Curator failed: {exc}[/red]")

    summary_lines = [
        f"Workflow complete: {entry_mode} entry through deterministic rating (gated)",
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


if __name__ == "__main__":
    asyncio.run(main())
