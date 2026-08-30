"""CLI adaptation for the workflow-level Curator."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from rich.console import Console

from discount_analyst.agents.curator.curator import create_curator_agent
from discount_analyst.agents.curator.user_prompt import create_user_prompt
from discount_analyst.agents.runtime.agent_names import AgentName
from discount_analyst.agents.runtime.streamed_agent_run import run_streamed_agent
from discount_analyst.application.allocations.assemble import (
    CompletedLaneBundle,
    assemble_curator_input,
    source_run_ids_by_ticker,
)
from discount_analyst.application.allocations.finalise import (
    finalise_curator_proposal,
)
from discount_analyst.config.ai_models_config import AIModelsConfig
from discount_analyst.domain.allocations.snapshot import CurrentPortfolioSnapshot
from discount_analyst.domain.model_selection.model_name import ModelName
from discount_analyst.entrypoints.cli.shared.artefacts import write_agent_json


def load_cli_portfolio_snapshot(path: Path) -> CurrentPortfolioSnapshot:
    return CurrentPortfolioSnapshot.model_validate_json(path.read_text())


async def run_cli_curator(
    *,
    console: Console,
    model_name: ModelName,
    snapshot: CurrentPortfolioSnapshot,
    lane_bundles: tuple[CompletedLaneBundle, ...],
) -> Path:
    curator_input = assemble_curator_input(lane_bundles, snapshot, date.today())
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_curator_agent(ai_models_config=ai_models_config)
    console.log(f"Running Curator (model: {model_name})...")
    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=create_user_prompt(curator_input=curator_input),
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
    )
    allocation = finalise_curator_proposal(
        outcome.output,
        curator_input,
        source_run_ids_by_ticker(lane_bundles),
    )
    out_path = write_agent_json(
        payload=allocation,
        model_name=model_name,
        agent_name=AgentName.CURATOR,
    )
    console.print(f"Saved allocation JSON: [dim]{out_path}[/dim]")
    return out_path
