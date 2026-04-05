"""Run the Researcher agent from Surveyor run output JSON selectors."""

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

from discount_analyst.agents.researcher.researcher import create_researcher_agent
from discount_analyst.agents.researcher.user_prompt import create_user_prompt
from discount_analyst.config.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.agents.common.streamed_agent_run import run_streamed_agent
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from scripts.common.cli import (
    add_agent_cli_model_argument,
    add_agent_cli_web_search_arguments,
)
from scripts.common.artifacts import write_agent_json
from scripts.common.run_outputs import (
    ResearcherRunOutput,
    SurveyorRunOutput,
    TurnUsage,
)
from scripts.common.usage import extract_turn_usage
from scripts.utils.setup_logfire import setup_logfire

setup_logfire()

console = Console()


@dataclass(frozen=True)
class Selector:
    surveyor_report_path: Path
    ticker: str | None
    raw: str


class CandidateTarget(NamedTuple):
    surveyor_report_path: Path
    candidate_index: int
    candidate: SurveyorCandidate


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
class FailedCandidateRun:
    ticker: str
    source_path: Path
    candidate_index: int
    error: str


class ResearcherArgs(BaseModel):
    model: ModelName
    use_perplexity: bool
    use_mcp_financial_data: bool
    selectors: list[Selector]


def _parse_selector(raw: str, parser: argparse.ArgumentParser) -> Selector:
    stripped = raw.strip()
    if not stripped:
        parser.error(
            "Invalid --surveyor-report-and-ticker value: empty selector. "
            "Expected '<surveyor_run_output.json>' or "
            "'<surveyor_run_output.json>:<TICKER>'."
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
                "'<surveyor_run_output.json>' or "
                "'<surveyor_run_output.json>:<TICKER>'."
            )
    else:
        report_part = stripped
        ticker_part = None

    path = Path(report_part).expanduser().resolve()
    if path.suffix.lower() != ".json":
        parser.error(
            f"Invalid selector '{raw}': expected a .json Surveyor run artifact path. "
            f"Got: {path}."
        )
    if not path.is_file():
        parser.error(
            f"Invalid selector '{raw}': Surveyor output file not found at {path}. "
            "Expected '<surveyor_run_output.json>' or "
            "'<surveyor_run_output.json>:<TICKER>'."
        )

    return Selector(surveyor_report_path=path, ticker=ticker_part, raw=raw)


def parse_args() -> ResearcherArgs:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Researcher agent for one or more candidates selected "
            "from Surveyor run output JSON."
        )
    )
    parser.add_argument(
        "--surveyor-report-and-ticker",
        action="append",
        required=True,
        dest="selectors",
        metavar="SELECTOR",
        help=(
            "Candidate selector (repeatable): either "
            "'<surveyor_run_output.json>' for all candidates in that run "
            "or '<surveyor_run_output.json>:<TICKER>' for one ticker."
        ),
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
    selectors = [_parse_selector(value, parser) for value in raw.selectors]
    return ResearcherArgs(
        model=raw.model,
        use_perplexity=raw.use_perplexity,
        use_mcp_financial_data=not raw.no_mcp,
        selectors=selectors,
    )


def load_surveyor_run_output(path: Path) -> SurveyorRunOutput:
    """Parse a Surveyor run output JSON artifact."""
    try:
        return SurveyorRunOutput.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise ValueError(
            f"Invalid Surveyor run output JSON shape at {path}: {exc}"
        ) from exc


def _resolve_targets_for_selector(selector: Selector) -> list[CandidateTarget]:
    run_output = load_surveyor_run_output(selector.surveyor_report_path)
    candidates = run_output.output.candidates

    if selector.ticker is None:
        duplicate_indexes_by_ticker: dict[str, list[int]] = {}
        for index, candidate in enumerate(candidates):
            duplicate_indexes_by_ticker.setdefault(
                candidate.ticker.casefold(), []
            ).append(index)
        for _, indexes in duplicate_indexes_by_ticker.items():
            if len(indexes) > 1:
                ticker_label = candidates[indexes[0]].ticker
                index_list = ", ".join(str(i) for i in indexes)
                console.print(
                    f"[yellow]Duplicate ticker '{ticker_label}' in "
                    f"{selector.surveyor_report_path}. Processing by candidate index "
                    f"order: {index_list}.[/yellow]"
                )
        return [
            CandidateTarget(
                surveyor_report_path=selector.surveyor_report_path,
                candidate_index=index,
                candidate=candidate,
            )
            for index, candidate in enumerate(candidates)
        ]

    ticker_folded = selector.ticker.casefold()
    matches = [
        CandidateTarget(
            surveyor_report_path=selector.surveyor_report_path,
            candidate_index=index,
            candidate=candidate,
        )
        for index, candidate in enumerate(candidates)
        if candidate.ticker.casefold() == ticker_folded
    ]
    if not matches:
        available = ", ".join(sorted({c.ticker for c in candidates})) or "<none>"
        raise ValueError(
            f"Ticker '{selector.ticker}' not found in {selector.surveyor_report_path}. "
            f"Available tickers: {available}."
        )
    if len(matches) > 1:
        indexes = ", ".join(str(match.candidate_index) for match in matches)
        console.print(
            f"[yellow]Duplicate ticker '{selector.ticker}' in "
            f"{selector.surveyor_report_path}. Processing by candidate index order: "
            f"{indexes}.[/yellow]"
        )
    return matches


def resolve_targets(selectors: list[Selector]) -> list[CandidateTarget]:
    """Resolve all selectors into an ordered candidate list."""
    targets: list[CandidateTarget] = []
    for selector in selectors:
        targets.extend(_resolve_targets_for_selector(selector))
    return targets


def _build_suffixes(targets: list[CandidateTarget]) -> list[str]:
    ticker_counts = Counter(target.candidate.ticker.casefold() for target in targets)
    ticker_seen: Counter[str] = Counter()
    suffixes: list[str] = []

    for target in targets:
        folded = target.candidate.ticker.casefold()
        ticker_seen[folded] += 1
        if ticker_counts[folded] > 1:
            suffixes.append(f"{target.candidate.ticker.upper()}-{ticker_seen[folded]}")
        else:
            suffixes.append(target.candidate.ticker.upper())
    return suffixes


def display_output(output: DeepResearchReport) -> None:
    """Print a concise Researcher summary panel/table."""
    candidate = output.candidate
    table = Table(title=f"Researcher Output - {candidate.ticker}", show_header=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Company", candidate.company_name)
    table.add_row("Exchange", candidate.exchange.value)
    table.add_row("Sector", candidate.sector)
    table.add_row("Narrative (dominant)", output.market_narrative.dominant_narrative)
    table.add_row(
        "Data gaps (remaining)",
        str(len(output.data_gaps_update.remaining_open_gaps)),
    )
    table.add_row(
        "Data gaps (material)",
        str(len(output.data_gaps_update.material_open_gaps)),
    )
    console.print(
        Panel.fit(
            "[bold green]Researcher Agent Output[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(table)


async def run_agent(
    *,
    model_name: ModelName,
    candidate: SurveyorCandidate,
    use_perplexity: bool,
    use_mcp_financial_data: bool,
) -> AgentRunResult:
    """Run the Researcher agent and return output with usage stats."""
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_researcher_agent(
        ai_models_config,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
    )
    user_prompt = create_user_prompt(surveyor_candidate=candidate)

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
    target: CandidateTarget,
    filename_suffix: str,
) -> Path:
    run_output = ResearcherRunOutput(
        ticker=target.candidate.ticker,
        model_name=model_name.value,
        source_surveyor_report=str(target.surveyor_report_path),
        source_candidate_index=target.candidate_index,
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
        agent_name=AgentName.RESEARCHER,
        filename_suffix=filename_suffix,
    )


def display_failure_summary(failures: list[FailedCandidateRun]) -> None:
    table = Table(
        title="Researcher Failures",
        show_header=True,
        header_style="bold red",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Candidate Index", style="yellow", no_wrap=True)
    table.add_column("Surveyor Report", style="magenta")
    table.add_column("Error", style="white")
    for failed in failures:
        table.add_row(
            failed.ticker,
            str(failed.candidate_index),
            str(failed.source_path),
            failed.error,
        )
    console.print(table)


async def main() -> None:
    args = parse_args()
    targets = resolve_targets(args.selectors)
    if not targets:
        raise SystemExit("No candidates selected to run Researcher.")

    suffixes = _build_suffixes(targets)
    failures: list[FailedCandidateRun] = []
    successes = 0

    for i, target in enumerate(targets):
        if i > 0:
            console.print("\n[bold]--- Next candidate ---[/bold]\n")

        if suffixes[i] != target.candidate.ticker.upper():
            console.print(
                f"[yellow]Duplicate ticker '{target.candidate.ticker}' detected; "
                f"using output suffix '{suffixes[i]}'.[/yellow]"
            )

        console.log(
            f"Running Researcher for {target.candidate.ticker} "
            f"(candidate_index={target.candidate_index}, "
            f"source={target.surveyor_report_path})..."
        )
        try:
            run_result = await run_agent(
                model_name=args.model,
                candidate=target.candidate,
                use_perplexity=args.use_perplexity,
                use_mcp_financial_data=args.use_mcp_financial_data,
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
                FailedCandidateRun(
                    ticker=target.candidate.ticker,
                    source_path=target.surveyor_report_path,
                    candidate_index=target.candidate_index,
                    error=str(exc),
                )
            )
            console.print(
                f"[red]Researcher failed for {target.candidate.ticker} "
                f"(candidate_index={target.candidate_index}). Continuing...[/red]"
            )
            console.print(f"[dim]{exc}[/dim]")

    console.print(
        Panel.fit(
            f"Completed Researcher batch\n"
            f"Successes: {successes}\n"
            f"Failures: {len(failures)}\n"
            f"Total candidates: {len(targets)}",
            border_style="cyan",
        )
    )
    if failures:
        display_failure_summary(failures)


if __name__ == "__main__":
    asyncio.run(main())
