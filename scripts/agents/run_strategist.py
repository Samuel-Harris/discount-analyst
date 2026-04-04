"""Run the Strategist agent from Researcher run output JSON selectors."""

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

from discount_analyst.agents.strategist.strategist import create_strategist_agent
from discount_analyst.agents.strategist.user_prompt import create_user_prompt
from discount_analyst.shared.config.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.shared.constants.agents import AgentName
from discount_analyst.shared.http.rate_limit_client import stream_with_retries
from discount_analyst.shared.schemas.researcher import DeepResearchReport
from discount_analyst.shared.schemas.strategist import MispricingThesis
from scripts.shared.cli import add_agent_cli_model_argument
from scripts.shared.outputs import write_agent_json
from scripts.shared.schemas.run_outputs import (
    ResearcherRunOutput,
    StrategistRunOutput,
    TurnUsage,
)
from scripts.shared.usage import extract_turn_usage
from scripts.utils.setup_logfire import setup_logfire

setup_logfire()

console = Console()


@dataclass(frozen=True)
class Selector:
    researcher_report_path: Path
    ticker: str | None
    raw: str


class ResearcherTarget(NamedTuple):
    researcher_report_path: Path
    run_output: ResearcherRunOutput


@dataclass
class AgentRunResult:
    output: MispricingThesis
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    turn_usage: list[TurnUsage]


@dataclass
class FailedStrategistRun:
    ticker: str
    source_path: Path
    error: str


class StrategistArgs(BaseModel):
    model: ModelName
    selectors: list[Selector]


def _parse_selector(raw: str, parser: argparse.ArgumentParser) -> Selector:
    stripped = raw.strip()
    if not stripped:
        parser.error(
            "Invalid --researcher-report-and-ticker value: empty selector. "
            "Expected '<researcher_run_output.json>' or "
            "'<researcher_run_output.json>:<TICKER>'."
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
                "'<researcher_run_output.json>' or "
                "'<researcher_run_output.json>:<TICKER>'."
            )
    else:
        report_part = stripped
        ticker_part = None

    path = Path(report_part).expanduser().resolve()
    if path.suffix.lower() != ".json":
        parser.error(
            f"Invalid selector '{raw}': expected a .json Researcher run artifact path. "
            f"Got: {path}."
        )
    if not path.is_file():
        parser.error(
            f"Invalid selector '{raw}': Researcher output file not found at {path}. "
            "Expected '<researcher_run_output.json>' or "
            "'<researcher_run_output.json>:<TICKER>'."
        )

    return Selector(researcher_report_path=path, ticker=ticker_part, raw=raw)


def parse_args() -> StrategistArgs:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Strategist agent for one or more Researcher run output JSON files."
        )
    )
    parser.add_argument(
        "--researcher-report-and-ticker",
        action="append",
        required=True,
        dest="selectors",
        metavar="SELECTOR",
        help=(
            "Researcher artifact selector (repeatable): either "
            "'<researcher_run_output.json>' for that run "
            "or '<researcher_run_output.json>:<TICKER>' to require a ticker match."
        ),
    )
    add_agent_cli_model_argument(parser)
    raw = parser.parse_args()
    selectors = [_parse_selector(value, parser) for value in raw.selectors]
    return StrategistArgs(model=raw.model, selectors=selectors)


def load_researcher_run_output(path: Path) -> ResearcherRunOutput:
    """Parse a Researcher run output JSON artifact."""
    try:
        return ResearcherRunOutput.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise ValueError(
            f"Invalid Researcher run output JSON shape at {path}: {exc}"
        ) from exc


def _resolve_targets_for_selector(selector: Selector) -> list[ResearcherTarget]:
    run_output = load_researcher_run_output(selector.researcher_report_path)
    if selector.ticker is None:
        return [ResearcherTarget(selector.researcher_report_path, run_output)]

    ticker_folded = selector.ticker.casefold()
    if run_output.ticker.casefold() != ticker_folded:
        raise ValueError(
            f"Ticker '{selector.ticker}' does not match Researcher artifact "
            f"{selector.researcher_report_path} (ticker={run_output.ticker})."
        )
    return [ResearcherTarget(selector.researcher_report_path, run_output)]


def resolve_targets(selectors: list[Selector]) -> list[ResearcherTarget]:
    """Resolve all selectors into an ordered target list."""
    targets: list[ResearcherTarget] = []
    for selector in selectors:
        targets.extend(_resolve_targets_for_selector(selector))
    return targets


def _build_suffixes(targets: list[ResearcherTarget]) -> list[str]:
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


def display_output(output: MispricingThesis) -> None:
    """Print a concise Strategist summary table."""
    table = Table(title=f"Strategist Output - {output.ticker}", show_header=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Company", output.company_name)
    table.add_row("Mispricing type", output.mispricing_type)
    table.add_row("Conviction", output.conviction_level)
    console.print(
        Panel.fit(
            "[bold green]Strategist Agent Output[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(table)


async def run_agent(
    *,
    model_name: ModelName,
    deep_research: DeepResearchReport,
) -> AgentRunResult:
    """Run the Strategist agent and return output with usage stats."""
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_strategist_agent(ai_models_config)
    surveyor_candidate = deep_research.candidate
    user_prompt = create_user_prompt(
        surveyor_candidate=surveyor_candidate,
        deep_research=deep_research,
    )

    start = time.perf_counter()
    async with stream_with_retries(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=ai_models_config.model.usage_limits,
    ) as result:
        async for message in result.stream_output():
            console.log(f"Streaming: {message}")
        output = await result.get_output()
        usage = result.usage()
        turn_usage = extract_turn_usage(result.all_messages())

    elapsed_s = time.perf_counter() - start
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
    target: ResearcherTarget,
    filename_suffix: str,
) -> Path:
    ro = target.run_output
    run_output = StrategistRunOutput(
        ticker=ro.ticker,
        model_name=model_name.value,
        source_surveyor_report=ro.source_surveyor_report,
        source_candidate_index=ro.source_candidate_index,
        source_researcher_report=str(target.researcher_report_path),
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
        agent_name=AgentName.STRATEGIST,
        filename_suffix=filename_suffix,
    )


def display_failure_summary(failures: list[FailedStrategistRun]) -> None:
    table = Table(
        title="Strategist Failures",
        show_header=True,
        header_style="bold red",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Researcher Report", style="magenta")
    table.add_column("Error", style="white")
    for failed in failures:
        table.add_row(failed.ticker, str(failed.source_path), failed.error)
    console.print(table)


async def main() -> None:
    args = parse_args()
    targets = resolve_targets(args.selectors)
    if not targets:
        raise SystemExit("No Researcher artifacts selected to run Strategist.")

    suffixes = _build_suffixes(targets)
    failures: list[FailedStrategistRun] = []
    successes = 0

    for i, target in enumerate(targets):
        if i > 0:
            console.print("\n[bold]--- Next target ---[/bold]\n")

        ro = target.run_output
        if suffixes[i] != ro.ticker.upper():
            console.print(
                f"[yellow]Duplicate ticker '{ro.ticker}' detected; "
                f"using output suffix '{suffixes[i]}'.[/yellow]"
            )

        console.log(
            f"Running Strategist for {ro.ticker} "
            f"(source={target.researcher_report_path})..."
        )
        try:
            run_result = await run_agent(
                model_name=args.model,
                deep_research=ro.output,
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
                FailedStrategistRun(
                    ticker=ro.ticker,
                    source_path=target.researcher_report_path,
                    error=str(exc),
                )
            )
            console.print(
                f"[red]Strategist failed for {ro.ticker}. Continuing...[/red]"
            )
            console.print(f"[dim]{exc}[/dim]")

    console.print(
        Panel.fit(
            f"Completed Strategist batch\n"
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
