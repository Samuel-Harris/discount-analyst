"""Run the closed-book Allocator from a complete AllocatorInput JSON file."""

import argparse
import asyncio
from pathlib import Path

from pydantic import BaseModel, ValidationError
from rich.console import Console

from discount_analyst.adapters.observability.script_setup import setup_logfire
from discount_analyst.agents.allocator.allocator import create_allocator_agent
from discount_analyst.agents.allocator.schema import AllocatorInput, AllocatorProposal
from discount_analyst.agents.allocator.user_prompt import create_user_prompt
from discount_analyst.agents.runtime.agent_names import AgentName
from discount_analyst.agents.runtime.streamed_agent_run import run_streamed_agent
from discount_analyst.config.ai_models_config import AIModelsConfig
from discount_analyst.domain.model_selection.model_name import ModelName
from discount_analyst.entrypoints.cli.shared.artefacts import write_agent_json
from discount_analyst.entrypoints.cli.shared.cli import add_agent_cli_model_argument

setup_logfire()

console = Console()


class AllocatorArgs(BaseModel):
    model: ModelName
    allocator_input: Path


def parse_args() -> AllocatorArgs:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Allocator from a complete AllocatorInput JSON file. "
            "The snapshot is required inside that payload; it is not optional."
        )
    )
    add_agent_cli_model_argument(parser)
    parser.add_argument(
        "allocator_input",
        type=Path,
        help="Path to a JSON file containing a complete AllocatorInput.",
    )
    raw = parser.parse_args()
    return AllocatorArgs(model=raw.model, allocator_input=raw.allocator_input)


def _load_allocator_input(path: Path) -> AllocatorInput:
    try:
        return AllocatorInput.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise ValueError(f"Invalid AllocatorInput JSON shape at {path}: {exc}") from exc


def display_output(output: AllocatorProposal) -> None:
    console.print(
        f"Allocator proposal for {output.allocation_date.isoformat()}: "
        f"{len(output.positions)} positions, cash target "
        f"{output.cash.target_weight_pct:.2f}%."
    )


async def main() -> None:
    args = parse_args()
    allocator_input = _load_allocator_input(args.allocator_input)
    ai_models_config = AIModelsConfig(model_name=args.model)
    agent = create_allocator_agent(ai_models_config=ai_models_config)
    console.log(f"Running Allocator agent (model: {args.model})...")
    outcome = await run_streamed_agent(
        agent=agent,
        user_prompt=create_user_prompt(allocator_input=allocator_input),
        usage_limits=ai_models_config.model.usage_limits,
        on_stream_chunk=lambda message: console.log(f"Streaming: {message}"),
    )
    display_output(outcome.output)
    out_path = write_agent_json(
        payload=outcome.output,
        model_name=args.model,
        agent_name=AgentName.ALLOCATOR,
    )
    console.print(f"\nSaved [dim]{out_path}[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
