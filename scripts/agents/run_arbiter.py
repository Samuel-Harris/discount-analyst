"""Run the Arbiter agent from Appraiser run output JSON selectors."""

import argparse
import asyncio
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import NamedTuple

from pydantic import BaseModel, ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from discount_analyst.agents.arbiter.arbiter import create_arbiter_agent
from discount_analyst.agents.arbiter.schema import (
    ArbiterDecision,
    ArbiterInput,
    ValuationResult,
)
from discount_analyst.agents.arbiter.user_prompt import create_user_prompt
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.agents.common.streamed_agent_run import run_streamed_agent
from discount_analyst.config.ai_models_config import AIModelsConfig, ModelName
from scripts.common.artefacts import write_agent_json
from scripts.common.cli import add_agent_cli_model_argument
from scripts.common.run_outputs import (
    AppraiserRunOutput,
    ArbiterRunOutput,
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
    appraiser_report_path: Path
    ticker: str | None
    raw: str


class ArbiterTarget(NamedTuple):
    appraiser_report_path: Path
    appraiser_run: AppraiserRunOutput
    arbiter_input: ArbiterInput


@dataclass
class AgentRunResult:
    output: ArbiterDecision
    elapsed_s: float
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    tool_calls: int
    turn_usage: list[TurnUsage]


class ArbiterCliArgs(BaseModel):
    model: ModelName
    selectors: list[Selector]
    is_existing_position: bool


@dataclass
class FailedArbiterRun:
    ticker: str
    source_path: Path
    error: str


def _parse_selector(raw: str, parser: argparse.ArgumentParser) -> Selector:
    stripped = raw.strip()
    if not stripped:
        parser.error(
            "Invalid --appraiser-report-and-ticker value: empty selector. "
            "Expected '<appraiser_run_output.json>' or "
            "'<appraiser_run_output.json>:<TICKER>'."
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
                "'<appraiser_run_output.json>' or "
                "'<appraiser_run_output.json>:<TICKER>'."
            )
    else:
        report_part = stripped
        ticker_part = None

    path = Path(report_part).expanduser().resolve()
    if path.suffix.lower() != ".json":
        parser.error(
            f"Invalid selector '{raw}': expected a .json Appraiser run artefact path. "
            f"Got: {path}."
        )
    if not path.is_file():
        parser.error(
            f"Invalid selector '{raw}': Appraiser output file not found at {path}. "
            "Expected '<appraiser_run_output.json>' or "
            "'<appraiser_run_output.json>:<TICKER>'."
        )

    return Selector(appraiser_report_path=path, ticker=ticker_part, raw=raw)


def parse_args() -> ArbiterCliArgs:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Arbiter agent for one or more Appraiser run output JSON files "
            "(requires a non-null dcf_result). Full human-facing output in workflows "
            "is wrapped as a Verdict."
        )
    )
    parser.add_argument(
        "--appraiser-report-and-ticker",
        action="append",
        required=True,
        dest="selectors",
        metavar="SELECTOR",
        help=(
            "Appraiser artefact selector (repeatable): either "
            "'<appraiser_run_output.json>' for that run "
            "or '<appraiser_run_output.json>:<TICKER>' to require a ticker match."
        ),
    )
    parser.add_argument(
        "--is-existing-position",
        action="store_true",
        help="Framing for recommended_action only (existing holding vs new candidate).",
    )
    add_agent_cli_model_argument(parser)
    raw = parser.parse_args()
    selectors = [_parse_selector(value, parser) for value in raw.selectors]
    return ArbiterCliArgs(
        model=raw.model,
        selectors=selectors,
        is_existing_position=raw.is_existing_position,
    )


def _load_appraiser_run_output(path: Path) -> AppraiserRunOutput:
    try:
        return AppraiserRunOutput.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise ValueError(
            f"Invalid Appraiser run output JSON shape at {path}: {exc}"
        ) from exc


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


def _resolve_target(
    selector: Selector,
    *,
    is_existing_position: bool,
) -> ArbiterTarget:
    appr = _load_appraiser_run_output(selector.appraiser_report_path)
    if selector.ticker is not None:
        folded = selector.ticker.casefold()
        if appr.ticker.casefold() != folded:
            raise ValueError(
                f"Ticker '{selector.ticker}' does not match Appraiser artefact "
                f"{selector.appraiser_report_path} (ticker={appr.ticker})."
            )
    if appr.dcf_result is None:
        raise ValueError(
            f"Arbiter requires a successful DCF in {selector.appraiser_report_path}; "
            "dcf_result is null (re-run Appraiser or fix DCF inputs)."
        )

    sentinel_path = Path(appr.source_sentinel_report).expanduser().resolve()
    surveyor_path = Path(appr.source_surveyor_report).expanduser().resolve()
    researcher_path = Path(appr.source_researcher_report).expanduser().resolve()
    strategist_path = Path(appr.source_strategist_report).expanduser().resolve()
    for label, p in (
        ("Sentinel", sentinel_path),
        ("Surveyor", surveyor_path),
        ("Researcher", researcher_path),
        ("Strategist", strategist_path),
    ):
        if not p.is_file():
            raise ValueError(
                f"Appraiser artefact {selector.appraiser_report_path} references "
                f"{label} report that is not a file: {p}"
            )

    sent = _load_sentinel_run_output(sentinel_path)
    surveyor = _load_surveyor_run_output(surveyor_path)
    idx = appr.source_candidate_index
    if idx < 0 or idx >= len(surveyor.output.candidates):
        raise ValueError(
            f"Appraiser artefact {selector.appraiser_report_path} references "
            f"candidate_index={idx} but Surveyor report has "
            f"{len(surveyor.output.candidates)} candidates ({surveyor_path})."
        )
    surveyor_candidate = surveyor.output.candidates[idx]
    researcher = _load_researcher_run_output(researcher_path)
    strategist = _load_strategist_run_output(strategist_path)

    valuation = ValuationResult(
        appraiser_output=appr.appraiser,
        dcf_result=appr.dcf_result,
    )
    arbiter_input = ArbiterInput(
        stock_candidate=surveyor_candidate,
        deep_research=researcher.output,
        thesis=strategist.output,
        evaluation=sent.output,
        valuation=valuation,
        risk_free_rate=appr.risk_free_rate,
        is_existing_position=is_existing_position,
    )
    return ArbiterTarget(
        appraiser_report_path=selector.appraiser_report_path,
        appraiser_run=appr,
        arbiter_input=arbiter_input,
    )


def resolve_targets(
    selectors: list[Selector],
    *,
    is_existing_position: bool,
) -> list[ArbiterTarget]:
    return [
        _resolve_target(s, is_existing_position=is_existing_position) for s in selectors
    ]


def _build_suffixes(targets: list[ArbiterTarget]) -> list[str]:
    ticker_counts = Counter(t.appraiser_run.ticker.casefold() for t in targets)
    ticker_seen: Counter[str] = Counter()
    suffixes: list[str] = []

    for target in targets:
        folded = target.appraiser_run.ticker.casefold()
        ticker_seen[folded] += 1
        if ticker_counts[folded] > 1:
            suffixes.append(
                f"{target.appraiser_run.ticker.upper()}-{ticker_seen[folded]}"
            )
        else:
            suffixes.append(target.appraiser_run.ticker.upper())
    return suffixes


def display_output(output: ArbiterDecision) -> None:
    table = Table(title=f"Arbiter — {output.ticker}", show_header=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Company", output.company_name)
    table.add_row("Rating", output.rating)
    table.add_row("Recommended action", output.recommended_action)
    table.add_row("Conviction", output.conviction)
    table.add_row(
        "Margin of safety (verdict)",
        output.margin_of_safety.margin_of_safety_verdict,
    )
    console.print(
        Panel.fit(
            "[bold green]Arbiter output[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(table)


async def run_agent(
    *,
    model_name: ModelName,
    arbiter_input: ArbiterInput,
) -> AgentRunResult:
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_arbiter_agent(ai_models_config)
    user_prompt = create_user_prompt(arbiter_input=arbiter_input)

    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
    )
    raw_out = outcome.output
    usage = outcome.usage
    turn_usage = extract_turn_usage(outcome.all_messages)
    elapsed_s = outcome.elapsed_s
    normalized = raw_out.model_copy(update={"decision_date": date.today().isoformat()})

    for turn in turn_usage:
        console.log(
            f"Turn {turn.turn} usage: in={turn.input_tokens} "
            f"out={turn.output_tokens} total={turn.total_tokens} "
            f"(cum_in={turn.cumulative_input_tokens} "
            f"cum_out={turn.cumulative_output_tokens})"
        )

    return AgentRunResult(
        output=normalized,
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
    target: ArbiterTarget,
    filename_suffix: str,
) -> Path:
    appr = target.appraiser_run
    run_output = ArbiterRunOutput(
        ticker=appr.ticker,
        model_name=model_name.value,
        risk_free_rate=appr.risk_free_rate,
        is_existing_position=target.arbiter_input.is_existing_position,
        source_surveyor_report=appr.source_surveyor_report,
        source_candidate_index=appr.source_candidate_index,
        source_researcher_report=appr.source_researcher_report,
        source_strategist_report=appr.source_strategist_report,
        source_sentinel_report=appr.source_sentinel_report,
        source_appraiser_report=str(target.appraiser_report_path.resolve()),
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
        agent_name=AgentName.ARBITER,
        filename_suffix=filename_suffix,
    )


def display_failure_summary(failures: list[FailedArbiterRun]) -> None:
    table = Table(
        title="Arbiter Failures",
        show_header=True,
        header_style="bold red",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Appraiser Report", style="magenta")
    table.add_column("Error", style="white")
    for failed in failures:
        table.add_row(failed.ticker, str(failed.source_path), failed.error)
    console.print(table)


async def main() -> None:
    args = parse_args()
    try:
        targets = resolve_targets(
            args.selectors, is_existing_position=args.is_existing_position
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if not targets:
        raise SystemExit("No Appraiser artefacts selected to run Arbiter.")

    suffixes = _build_suffixes(targets)
    failures: list[FailedArbiterRun] = []
    successes = 0

    for i, target in enumerate(targets):
        if i > 0:
            console.print("\n[bold]--- Next target ---[/bold]\n")

        appr = target.appraiser_run
        if suffixes[i] != appr.ticker.upper():
            console.print(
                f"[yellow]Duplicate ticker '{appr.ticker}' detected; "
                f"using output suffix '{suffixes[i]}'.[/yellow]"
            )

        console.log(
            f"Running Arbiter for {appr.ticker} "
            f"(source={target.appraiser_report_path})..."
        )
        try:
            run_result = await run_agent(
                model_name=args.model,
                arbiter_input=target.arbiter_input,
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
                FailedArbiterRun(
                    ticker=appr.ticker,
                    source_path=target.appraiser_report_path,
                    error=str(exc),
                )
            )
            console.print(f"[red]Arbiter failed for {appr.ticker}. Continuing...[/red]")
            console.print(f"[dim]{exc}[/dim]")

    console.print(
        Panel.fit(
            f"Completed Arbiter batch\n"
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
