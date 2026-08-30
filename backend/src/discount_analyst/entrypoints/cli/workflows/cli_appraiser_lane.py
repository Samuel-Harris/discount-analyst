"""CLI Appraiser lane: valuation plus deterministic rating-table Verdict."""

from datetime import date

from rich.console import Console

from discount_analyst.agents.appraiser.schema import AppraiserInput, AppraiserOutput
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.runtime.terminal_run import TerminalRunOptions
from discount_analyst.agents.sentinel.schema import EvaluationReport
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.application.decisions.builders import (
    build_rating_table_decision,
    verdict_from_decision,
)
from discount_analyst.application.workflows.appraiser_run_context import (
    AppraiserRunContext,
)
from discount_analyst.domain.decisions.margin_of_safety import MarginOfSafetyAssessment
from discount_analyst.domain.decisions.schema import Verdict
from discount_analyst.domain.model_selection.model_name import ModelName
from discount_analyst.entrypoints.cli.agents.run_appraiser import (
    display_agent_output,
    run_agent,
    save_run_output,
)


async def run_cli_appraiser_lane(
    *,
    console: Console,
    model: ModelName,
    risk_free_rate_pct: float,
    use_perplexity: bool,
    use_mcp_financial_data: bool,
    is_existing_position: bool,
    terminal: TerminalRunOptions,
    candidate: SurveyorCandidate,
    index: int,
    source_entry_report_path: str,
    researcher_out_path: str,
    strat_path: str,
    sentinel_path: str,
    filename_suffix: str,
    deep_research: DeepResearchReport,
    thesis: MispricingThesis,
    evaluation: EvaluationReport,
    verdicts: list[Verdict],
) -> tuple[Verdict, AppraiserOutput]:
    appraiser_input = AppraiserInput(
        lane_context=candidate.to_lane_context(),
        deep_research=deep_research,
        thesis=thesis,
        evaluation=evaluation,
        risk_free_rate_pct=risk_free_rate_pct,
    )
    run_context = AppraiserRunContext(
        lane_context=candidate.to_lane_context(),
        risk_free_rate_pct=risk_free_rate_pct,
        model=model,
    )
    agent_result = await run_agent(
        run_context,
        appraiser_input,
        use_perplexity=use_perplexity,
        use_mcp_financial_data=use_mcp_financial_data,
        terminal=terminal,
    )
    display_agent_output(agent_result.output)
    appraiser_out_path = save_run_output(
        run_context,
        agent_result.output,
        agent_result,
        source_surveyor_report=source_entry_report_path,
        source_candidate_index=index,
        source_researcher_report=researcher_out_path,
        source_strategist_report=strat_path,
        source_sentinel_report=sentinel_path,
        filename_suffix=filename_suffix,
    )
    console.print(f"Saved Appraiser output: [dim]{appraiser_out_path}[/dim]")

    margin_of_safety = MarginOfSafetyAssessment.from_distribution(
        agent_result.output.valuation_distribution
    )
    rating_decision = build_rating_table_decision(
        lane_context=candidate.to_lane_context(),
        thesis=thesis,
        evaluation=evaluation,
        margin_of_safety=margin_of_safety,
        is_existing_position=is_existing_position,
        decision_date=date.today().isoformat(),
    )
    verdict = verdict_from_decision(rating_decision)
    verdicts.append(verdict)
    return verdict, agent_result.output
