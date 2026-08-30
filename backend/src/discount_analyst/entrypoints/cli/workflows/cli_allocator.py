"""CLI adaptation for the workflow-level Allocator."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from rich.console import Console

from discount_analyst.agents.allocator.allocator import create_allocator_agent
from discount_analyst.agents.allocator.user_prompt import create_user_prompt
from discount_analyst.agents.runtime.agent_names import AgentName
from discount_analyst.agents.runtime.streamed_agent_run import run_streamed_agent
from discount_analyst.application.allocations.assemble import (
    CompletedLaneBundle,
    assemble_allocator_input,
)
from discount_analyst.application.allocations.finalise import (
    finalise_allocator_proposal,
)
from discount_analyst.config.ai_models_config import AIModelsConfig
from discount_analyst.domain.allocations.snapshot import CurrentPortfolioSnapshot
from discount_analyst.domain.model_selection.model_name import ModelName
from discount_analyst.entrypoints.cli.shared.artefacts import write_agent_json


def load_cli_portfolio_snapshot(path: Path) -> CurrentPortfolioSnapshot:
    return CurrentPortfolioSnapshot.model_validate_json(path.read_text())


async def run_cli_allocator(
    *,
    console: Console,
    model_name: ModelName,
    snapshot: CurrentPortfolioSnapshot,
    lane_bundles: tuple[CompletedLaneBundle, ...],
) -> Path:
    allocator_input = assemble_allocator_input(lane_bundles, snapshot, date.today())
    ai_models_config = AIModelsConfig(model_name=model_name)
    agent = create_allocator_agent(ai_models_config=ai_models_config)
    console.log(f"Running Allocator (model: {model_name})...")
    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=create_user_prompt(allocator_input=allocator_input),
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
    )
    allocation = finalise_allocator_proposal(
        outcome.output, allocator_input, lane_bundles
    )
    out_path = write_agent_json(
        payload=allocation,
        model_name=model_name,
        agent_name=AgentName.ALLOCATOR,
    )
    console.print(f"Saved allocation JSON: [dim]{out_path}[/dim]")
    return out_path
