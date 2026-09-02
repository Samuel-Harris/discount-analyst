"""Run the closed-book Curator from a complete CuratorInput JSON file."""

import argparse
import asyncio
from pathlib import Path

from pydantic import BaseModel, ValidationError
from rich.console import Console

from discount_analyst.adapters.observability.script_setup import setup_logfire
from discount_analyst.agents.curator.curator import create_curator_agent
from discount_analyst.agents.curator.schema import CuratorInput, CuratorProposal
from discount_analyst.agents.curator.user_prompt import create_user_prompt
from discount_analyst.agents.runtime.agent_names import AgentName
from discount_analyst.agents.runtime.streamed_agent_run import run_streamed_agent
from discount_analyst.config.ai_models_config import AIModelsConfig
from discount_analyst.config.settings import settings
from discount_analyst.domain.model_selection.model_name import ModelName
from discount_analyst.entrypoints.cli.shared.artefacts import write_agent_json
from discount_analyst.entrypoints.cli.shared.cli import add_agent_cli_model_argument

setup_logfire()

console = Console()


class CuratorArgs(BaseModel):
    model: ModelName
    curator_input: Path


def parse_args() -> CuratorArgs:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Curator from a complete CuratorInput JSON file. "
            "The snapshot is required inside that payload; it is not optional."
        )
    )
    add_agent_cli_model_argument(
        parser, default=settings.agent_default_models.curator
    )
    parser.add_argument(
        "curator_input",
        type=Path,
        help="Path to a JSON file containing a complete CuratorInput.",
    )
    raw = parser.parse_args()
    return CuratorArgs(model=raw.model, curator_input=raw.curator_input)


def _load_curator_input(path: Path) -> CuratorInput:
    try:
        return CuratorInput.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise ValueError(f"Invalid CuratorInput JSON shape at {path}: {exc}") from exc


def display_output(output: CuratorProposal) -> None:
    console.print(
        f"Curator proposal for {output.allocation_date.isoformat()}: "
        f"{len(output.positions)} positions, cash target "
        f"{output.cash.target_weight_pct:.2f}%."
    )


async def main() -> None:
    args = parse_args()
    curator_input = _load_curator_input(args.curator_input)
    ai_models_config = AIModelsConfig(model_name=args.model)
    agent = create_curator_agent(ai_models_config=ai_models_config)
    console.log(f"Running Curator agent (model: {args.model})...")
    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=create_user_prompt(curator_input=curator_input),
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
    )
    display_output(outcome.output)
    out_path = write_agent_json(
        payload=outcome.output,
        model_name=args.model,
        agent_name=AgentName.CURATOR,
    )
    console.print(f"\nSaved [dim]{out_path}[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
