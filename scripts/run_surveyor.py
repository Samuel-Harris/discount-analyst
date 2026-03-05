"""Run the Surveyor agent to discover cheap small-cap stock candidates."""

import argparse
import asyncio
import time
from datetime import datetime
from pathlib import Path

import logfire
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from discount_analyst.shared.config.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.shared.config.settings import settings
from discount_analyst.shared.http.rate_limit_client import stream_with_retries
from discount_analyst.surveyor.data_types import SurveyorOutput
from discount_analyst.surveyor.surveyor import create_surveyor_agent
from discount_analyst.surveyor.user_prompt import USER_PROMPT
from scripts.shared import SurveyorRunOutput, write_surveyor_output

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_OUTPUTS_DIR = _PROJECT_ROOT / "outputs"

logfire.configure(token=settings.pydantic.logfire_api_key, scrubbing=False)
logfire.instrument_pydantic_ai()

console = Console()


class SurveyorArgs(BaseModel):
    model: ModelName = Field(
        default=ModelName.CLAUDE_SONNET_4_6,
        description="AI model to use",
    )
    no_perplexity: bool = Field(
        default=False,
        description="Use model-native web search instead of Perplexity API",
    )
    no_mcp: bool = Field(
        default=False,
        description="Disable EODHD/FMP MCP financial data tools (required for Google models)",
    )


def parse_args() -> SurveyorArgs:
    parser = argparse.ArgumentParser(
        description="Run the Surveyor agent to discover cheap small-cap stock candidates."
    )
    parser.add_argument(
        "--model",
        type=ModelName,
        choices=[e.value for e in ModelName],
        default=ModelName.CLAUDE_SONNET_4_6,
        help=f"AI model to use (default: {ModelName.CLAUDE_SONNET_4_6})",
    )
    parser.add_argument(
        "--no-perplexity",
        action="store_true",
        help="Use model-native web search instead of Perplexity API",
    )
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="Disable EODHD/FMP MCP financial data tools (required for Google models)",
    )
    raw = parser.parse_args()
    return SurveyorArgs(
        model=raw.model,
        no_perplexity=raw.no_perplexity,
        no_mcp=raw.no_mcp,
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
        ai_models_config,
        use_perplexity=not args.no_perplexity,
        use_mcp_financial_data=not args.no_mcp,
    )

    console.log(f"Running Surveyor agent (model: {args.model})...")
    start = time.perf_counter()

    async with stream_with_retries(
        agent=agent,
        user_prompt=USER_PROMPT,
        usage_limits=ai_models_config.model.usage_limits,
    ) as result:
        async for message in result.stream_output():
            console.log(f"Streaming: {message}")
        output = await result.get_output()
        usage = result.usage()

    elapsed_s = time.perf_counter() - start
    console.log(
        f"Completed in {elapsed_s:.1f}s "
        f"(input: {usage.input_tokens}, output: {usage.output_tokens} tokens)"
    )

    display_output(output)

    run_output = SurveyorRunOutput(
        model_name=args.model.value,
        elapsed_s=elapsed_s,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        output=output,
    )
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    out_path = write_surveyor_output(
        run_output=run_output,
        timestamp=timestamp,
        output_dir=_OUTPUTS_DIR,
    )
    console.print(f"\nSaved [dim]{out_path}[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
