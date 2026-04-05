"""Run the Surveyor agent to discover cheap small-cap stock candidates."""

import argparse
import asyncio

from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from discount_analyst.config.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.agents.common.streamed_agent_run import run_streamed_agent
from discount_analyst.agents.surveyor.schema import SurveyorOutput
from discount_analyst.agents.surveyor.surveyor import create_surveyor_agent
from discount_analyst.agents.surveyor.user_prompt import USER_PROMPT
from scripts.common.cli import (
    add_agent_cli_model_argument,
    add_agent_cli_web_search_arguments,
)
from scripts.common.artifacts import write_agent_json
from scripts.common.run_outputs import SurveyorRunOutput
from scripts.common.usage import extract_turn_usage

from scripts.utils.setup_logfire import setup_logfire

setup_logfire()

console = Console()


class SurveyorArgs(BaseModel):
    model: ModelName
    use_perplexity: bool
    use_mcp_financial_data: bool


def parse_args() -> SurveyorArgs:
    parser = argparse.ArgumentParser(
        description="Run the Surveyor agent to discover cheap small-cap stock candidates."
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
    return SurveyorArgs(
        model=raw.model,
        use_perplexity=raw.use_perplexity,
        use_mcp_financial_data=not raw.no_mcp,
    )


def display_output(output: SurveyorOutput) -> None:
    """Print the Surveyor agent output."""
    table = Table(
        title="Cheap Small-Cap Stock Candidates",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Exchange", style="yellow")
    table.add_column("Market Cap", justify="right", style="blue")
    table.add_column("Rationale", style="white")

    for c in output.candidates:
        table.add_row(
            c.ticker,
            c.company_name,
            c.exchange.value,
            c.market_cap_display,
            c.rationale,
        )

    console.print("\n")
    console.print(
        Panel.fit(
            "[bold green]Surveyor Agent Output[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(table)


async def main() -> None:
    args = parse_args()

    ai_models_config = AIModelsConfig(model_name=args.model)
    agent = create_surveyor_agent(
        ai_models_config=ai_models_config,
        use_perplexity=args.use_perplexity,
        use_mcp_financial_data=args.use_mcp_financial_data,
    )

    console.log(f"Running Surveyor agent (model: {args.model})...")

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
    console.log(
        f"Completed in {elapsed_s:.1f}s "
        f"(input: {usage.input_tokens}, output: {usage.output_tokens} tokens)"
    )
    for turn in turn_usage:
        console.log(
            f"Turn {turn.turn} usage: in={turn.input_tokens} "
            f"out={turn.output_tokens} total={turn.total_tokens} "
            f"(cum_in={turn.cumulative_input_tokens} "
            f"cum_out={turn.cumulative_output_tokens})"
        )

    display_output(output)

    run_output = SurveyorRunOutput(
        model_name=args.model.value,
        elapsed_s=elapsed_s,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        turn_usage=turn_usage,
        output=output,
    )
    out_path = write_agent_json(
        payload=run_output,
        model_name=args.model,
        agent_name=AgentName.SURVEYOR,
    )
    console.print(f"\nSaved [dim]{out_path}[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
