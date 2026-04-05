"""Run the Sentinel agent from Strategist run output JSON selectors."""

import argparse
import asyncio
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from pydantic import BaseModel, ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from discount_analyst.agents.sentinel.schema import (
    EvaluationReport,
    sentinel_proceeds_to_valuation,
)
from discount_analyst.agents.sentinel.sentinel import create_sentinel_agent
from discount_analyst.agents.sentinel.user_prompt import create_user_prompt
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.agents.common.streamed_agent_run import run_streamed_agent
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.config.ai_models_config import AIModelsConfig, ModelName
from scripts.common.artifacts import write_agent_json
from scripts.common.cli import add_agent_cli_model_argument
from scripts.common.run_outputs import (
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


@dataclass(frozen=True)
class Selector:
    strategist_report_path: Path
    ticker: str | None
    raw: str


class SentinelTarget(NamedTuple):
    strategist_report_path: Path
    run_output: StrategistRunOutput
    surveyor_candidate: SurveyorCandidate
    deep_research: DeepResearchReport


@dataclass
class AgentRunResult:
    output: EvaluationReport
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    turn_usage: list[TurnUsage]


@dataclass
class FailedSentinelRun:
    ticker: str
    source_path: Path
    error: str


class SentinelArgs(BaseModel):
    model: ModelName
    selectors: list[Selector]


def _parse_selector(raw: str, parser: argparse.ArgumentParser) -> Selector:
    stripped = raw.strip()
    if not stripped:
        parser.error(
            "Invalid --strategist-report-and-ticker value: empty selector. "
            "Expected '<strategist_run_output.json>' or "
            "'<strategist_run_output.json>:<TICKER>'."
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
                "'<strategist_run_output.json>' or "
                "'<strategist_run_output.json>:<TICKER>'."
            )
    else:
        report_part = stripped
        ticker_part = None

    path = Path(report_part).expanduser().resolve()
    if path.suffix.lower() != ".json":
        parser.error(
            f"Invalid selector '{raw}': expected a .json Strategist run artifact path. "
            f"Got: {path}."
        )
    if not path.is_file():
        parser.error(
            f"Invalid selector '{raw}': Strategist output file not found at {path}. "
            "Expected '<strategist_run_output.json>' or "
            "'<strategist_run_output.json>:<TICKER>'."
        )

    return Selector(strategist_report_path=path, ticker=ticker_part, raw=raw)


def parse_args() -> SentinelArgs:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Sentinel agent for one or more Strategist run output JSON files."
        )
    )
    parser.add_argument(
        "--strategist-report-and-ticker",
        action="append",
        required=True,
        dest="selectors",
        metavar="SELECTOR",
        help=(
            "Strategist artifact selector (repeatable): either "
            "'<strategist_run_output.json>' for that run "
            "or '<strategist_run_output.json>:<TICKER>' to require a ticker match."
        ),
    )
    add_agent_cli_model_argument(parser)
    raw = parser.parse_args()
    selectors = [_parse_selector(value, parser) for value in raw.selectors]
    return SentinelArgs(model=raw.model, selectors=selectors)


def load_strategist_run_output(path: Path) -> StrategistRunOutput:
    """Parse a Strategist run output JSON artifact."""
    try:
        return StrategistRunOutput.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise ValueError(
            f"Invalid Strategist run output JSON shape at {path}: {exc}"
        ) from exc


def load_surveyor_run_output(path: Path) -> SurveyorRunOutput:
    try:
        return SurveyorRunOutput.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise ValueError(
            f"Invalid Surveyor run output JSON shape at {path}: {exc}"
        ) from exc


def load_researcher_run_output(path: Path) -> ResearcherRunOutput:
    try:
        return ResearcherRunOutput.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise ValueError(
            f"Invalid Researcher run output JSON shape at {path}: {exc}"
        ) from exc


def _resolve_targets_for_selector(selector: Selector) -> list[SentinelTarget]:
    so = load_strategist_run_output(selector.strategist_report_path)
    if selector.ticker is not None:
        ticker_folded = selector.ticker.casefold()
        if so.ticker.casefold() != ticker_folded:
            raise ValueError(
                f"Ticker '{selector.ticker}' does not match Strategist artifact "
                f"{selector.strategist_report_path} (ticker={so.ticker})."
            )

    surveyor_path = Path(so.source_surveyor_report).expanduser().resolve()
    researcher_path = Path(so.source_researcher_report).expanduser().resolve()
    surveyor = load_surveyor_run_output(surveyor_path)
    idx = so.source_candidate_index
    if idx < 0 or idx >= len(surveyor.output.candidates):
        raise ValueError(
            f"Strategist artifact {selector.strategist_report_path} references "
            f"candidate_index={idx} but Surveyor report has "
            f"{len(surveyor.output.candidates)} candidates ({surveyor_path})."
        )
    surveyor_candidate = surveyor.output.candidates[idx]
    researcher = load_researcher_run_output(researcher_path)
    deep_research = researcher.output

    return [
        SentinelTarget(
            strategist_report_path=selector.strategist_report_path,
            run_output=so,
            surveyor_candidate=surveyor_candidate,
            deep_research=deep_research,
        )
    ]


def resolve_targets(selectors: list[Selector]) -> list[SentinelTarget]:
    """Resolve all selectors into an ordered target list."""
    targets: list[SentinelTarget] = []
    for selector in selectors:
        targets.extend(_resolve_targets_for_selector(selector))
    return targets


def _build_suffixes(targets: list[SentinelTarget]) -> list[str]:
    ticker_counts = Counter(target.run_output.ticker.casefold() for target in targets)
    ticker_seen: Counter[str] = Counter()
    suffixes: list[str] = []

    for target in targets:
        folded = target.run_output.ticker.casefold()
        ticker_seen[folded] += 1
        if ticker_counts[folded] > 1:
            suffixes.append(f"{target.run_output.ticker.upper()}-{ticker_seen[folded]}")
        else:
            suffixes.append(target.run_output.ticker.upper())
    return suffixes


def display_output(output: EvaluationReport) -> None:
    """Print a concise Sentinel summary table."""
    table = Table(title=f"Sentinel Output - {output.ticker}", show_header=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Company", output.company_name)
    table.add_row("Thesis verdict", output.thesis_verdict)
    table.add_row(
        "Valuation gate (derived)",
        (
            "Proceed to valuation"
            if sentinel_proceeds_to_valuation(output.thesis_verdict)
            else "Do not proceed"
        ),
    )
    console.print(
        Panel.fit(
            "[bold green]Sentinel Agent Output[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(table)


async def run_agent(
    *,
    model_name: ModelName,
    surveyor_candidate: SurveyorCandidate,
    deep_research: DeepResearchReport,
    thesis: MispricingThesis,
) -> AgentRunResult:
    """Run the Sentinel agent and return output with usage stats."""
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_sentinel_agent(ai_models_config)
    user_prompt = create_user_prompt(
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
    for turn in turn_usage:
        console.log(
            f"Turn {turn.turn} usage: in={turn.input_tokens} "
            f"out={turn.output_tokens} total={turn.total_tokens} "
            f"(cum_in={turn.cumulative_input_tokens} "
            f"cum_out={turn.cumulative_output_tokens})"
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


def save_run_output(
    *,
    run_result: AgentRunResult,
    model_name: ModelName,
    target: SentinelTarget,
    filename_suffix: str,
) -> Path:
    so = target.run_output
    run_output = SentinelRunOutput(
        ticker=so.ticker,
        model_name=model_name.value,
        source_surveyor_report=so.source_surveyor_report,
        source_candidate_index=so.source_candidate_index,
        source_researcher_report=so.source_researcher_report,
        source_strategist_report=str(target.strategist_report_path),
        elapsed_s=run_result.elapsed_s,
        input_tokens=run_result.input_tokens,
        output_tokens=run_result.output_tokens,
        cache_write_tokens=run_result.cache_write_tokens,
        cache_read_tokens=run_result.cache_read_tokens,
        tool_calls=run_result.tool_calls,
        turn_usage=run_result.turn_usage,
        output=run_result.output,
    )
    return write_agent_json(
        payload=run_output,
        model_name=model_name,
        agent_name=AgentName.SENTINEL,
        filename_suffix=filename_suffix,
    )


def display_failure_summary(failures: list[FailedSentinelRun]) -> None:
    table = Table(
        title="Sentinel Failures",
        show_header=True,
        header_style="bold red",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Strategist Report", style="magenta")
    table.add_column("Error", style="white")
    for failed in failures:
        table.add_row(failed.ticker, str(failed.source_path), failed.error)
    console.print(table)


async def main() -> None:
    args = parse_args()
    targets = resolve_targets(args.selectors)
    if not targets:
        raise SystemExit("No Strategist artifacts selected to run Sentinel.")

    suffixes = _build_suffixes(targets)
    failures: list[FailedSentinelRun] = []
    successes = 0

    for i, target in enumerate(targets):
        if i > 0:
            console.print("\n[bold]--- Next target ---[/bold]\n")

        so = target.run_output
        if suffixes[i] != so.ticker.upper():
            console.print(
                f"[yellow]Duplicate ticker '{so.ticker}' detected; "
                f"using output suffix '{suffixes[i]}'.[/yellow]"
            )

        console.log(
            f"Running Sentinel for {so.ticker} "
            f"(source={target.strategist_report_path})..."
        )
        try:
            run_result = await run_agent(
                model_name=args.model,
                surveyor_candidate=target.surveyor_candidate,
                deep_research=target.deep_research,
                thesis=so.output,
            )
            display_output(run_result.output)
            out_path = save_run_output(
                run_result=run_result,
                model_name=args.model,
                target=target,
                filename_suffix=suffixes[i],
            )
            successes += 1
            console.print(f"Saved [dim]{out_path}[/dim]")
        except Exception as exc:
            failures.append(
                FailedSentinelRun(
                    ticker=so.ticker,
                    source_path=target.strategist_report_path,
                    error=str(exc),
                )
            )
            console.print(f"[red]Sentinel failed for {so.ticker}. Continuing...[/red]")
            console.print(f"[dim]{exc}[/dim]")

    console.print(
        Panel.fit(
            f"Completed Sentinel batch\n"
            f"Successes: {successes}\n"
            f"Failures: {len(failures)}\n"
            f"Total targets: {len(targets)}",
            border_style="cyan",
        )
    )
    if failures:
        display_failure_summary(failures)


if __name__ == "__main__":
    asyncio.run(main())
