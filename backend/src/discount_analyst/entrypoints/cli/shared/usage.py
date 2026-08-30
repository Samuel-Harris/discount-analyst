"""Extract token usage from pydantic-ai message history."""

from pydantic_ai.messages import ModelMessage

from discount_analyst.agents.runtime.turn_usage import iter_model_response_token_usage
from discount_analyst.entrypoints.cli.shared.run_outputs import TurnUsage


def extract_turn_usage(messages: list[ModelMessage]) -> list[TurnUsage]:
    """Extract per-turn usage by walking ModelResponse messages in order."""
    turns: list[TurnUsage] = []
    cumulative_input = 0
    cumulative_output = 0
    cumulative_total = 0

    for usage in iter_model_response_token_usage(messages):
        cumulative_input += usage.input_tokens
        cumulative_output += usage.output_tokens
        cumulative_total += usage.total_tokens
        turns.append(
            TurnUsage(
                turn=len(turns) + 1,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_write_tokens=usage.cache_write_tokens,
                cache_read_tokens=usage.cache_read_tokens,
                total_tokens=usage.total_tokens,
                cumulative_input_tokens=cumulative_input,
                cumulative_output_tokens=cumulative_output,
                cumulative_total_tokens=cumulative_total,
            )
        )

    return turns
