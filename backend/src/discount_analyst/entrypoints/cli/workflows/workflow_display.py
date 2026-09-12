"""Rich tables and failure summaries for the full CLI workflow."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.sentinel.schema import EvaluationReport
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.domain.decisions.schema import AppraisedDecision

console = Console()


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
class FailedProfilerRun:
    ticker: str
    candidate_index: int
    error: str


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


def display_researcher_output(
    output: DeepResearchReport, *, candidate: SurveyorCandidate
) -> None:
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
        "Red-flag screen",
        output.red_flag_screen.overall_red_flag_verdict.value,
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


def display_verdicts_table(verdicts: list[AppraisedDecision]) -> None:
    """Portfolio-style summary: one row per AppraisedDecision."""
    if not verdicts:
        return
    table = Table(
        title="Appraised lanes",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Company", style="green")
    table.add_column("Decision", style="blue")
    table.add_column("Existing", justify="center")
    for decision in verdicts:
        table.add_row(
            decision.ticker,
            decision.company_name,
            "Appraised",
            "Y" if decision.is_existing_position else "N",
        )
    console.print(table)
