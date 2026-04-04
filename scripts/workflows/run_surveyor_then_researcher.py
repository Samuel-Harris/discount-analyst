"""Run Surveyor once, then Researcher sequentially for each candidate."""

import argparse
import asyncio
from collections import Counter
from dataclasses import dataclass

from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from discount_analyst.agents.researcher.researcher import create_researcher_agent
from discount_analyst.agents.researcher.user_prompt import create_user_prompt
from discount_analyst.agents.surveyor.surveyor import create_surveyor_agent
from discount_analyst.agents.surveyor.user_prompt import USER_PROMPT
from discount_analyst.shared.ai.streamed_agent_run import run_streamed_agent
from discount_analyst.shared.config.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.shared.constants.agents import AgentName
from discount_analyst.shared.schemas.researcher import DeepResearchReport
from discount_analyst.shared.schemas.surveyor import SurveyorCandidate, SurveyorOutput
from scripts.shared.cli import (
    add_agent_cli_model_argument,
    add_agent_cli_web_search_arguments,
)
from scripts.shared.outputs import write_agent_json
from scripts.shared.schemas.run_outputs import (
    ResearcherRunOutput,
    SurveyorRunOutput,
    TurnUsage,
)
from scripts.shared.usage import extract_turn_usage
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
class FailedCandidateRun:
    ticker: str
    candidate_index: int
    error: str


class WorkflowArgs(BaseModel):
    model: ModelName
    use_perplexity: bool
    use_mcp_financial_data: bool


def parse_args() -> WorkflowArgs:
    parser = argparse.ArgumentParser(
        description="Run Surveyor once, then Researcher sequentially for each candidate."
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
    return WorkflowArgs(
        model=raw.model,
        use_perplexity=raw.use_perplexity,
        use_mcp_financial_data=not raw.no_mcp,
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


def display_surveyor_output(output: SurveyorOutput) -> None:
    table = Table(
        title="Surveyor Candidates",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Exchange", style="yellow")
    table.add_column("Market Cap", style="blue", justify="right")
    for candidate in output.candidates:
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


async def main() -> None:
    args = parse_args()
    surveyor_run_output, surveyor_path = await run_surveyor_once(
        model_name=args.model,
        use_perplexity=args.use_perplexity,
        use_mcp_financial_data=args.use_mcp_financial_data,
    )
    candidates = surveyor_run_output.output.candidates
    display_surveyor_output(surveyor_run_output.output)

    console.print(f"\nSaved Surveyor output: [dim]{surveyor_path}[/dim]\n")
    console.log(
        f"Starting sequential Researcher runs for {len(candidates)} candidates..."
    )

    suffixes = _build_researcher_suffixes(candidates)
    failures: list[FailedCandidateRun] = []
    successes = 0

    for index, candidate in enumerate(candidates):
        if index > 0:
            console.print("\n[bold]--- Next candidate ---[/bold]\n")
        if suffixes[index] != candidate.ticker.upper():
            console.print(
                f"[yellow]Duplicate ticker '{candidate.ticker}' detected; "
                f"using output suffix '{suffixes[index]}'.[/yellow]"
            )

        try:
            run_result = await run_researcher_once(
                model_name=args.model,
                surveyor_report_path=surveyor_path,
                candidate_index=index,
                candidate=candidate,
                use_perplexity=args.use_perplexity,
                use_mcp_financial_data=args.use_mcp_financial_data,
            )
            display_researcher_output(run_result.output)
            out_path = save_researcher_output(
                model_name=args.model,
                surveyor_report_path=surveyor_path,
                candidate_index=index,
                candidate=candidate,
                run_result=run_result,
                filename_suffix=suffixes[index],
            )
            successes += 1
            console.print(f"Saved Researcher output: [dim]{out_path}[/dim]")
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

    console.print(
        Panel.fit(
            f"Workflow complete: Surveyor then Researcher\n"
            f"Candidates: {len(candidates)}\n"
            f"Researcher successes: {successes}\n"
            f"Researcher failures: {len(failures)}",
            border_style="cyan",
        )
    )
    if failures:
        display_failure_summary(failures)


if __name__ == "__main__":
    asyncio.run(main())
