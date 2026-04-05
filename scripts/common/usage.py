"""Extract token usage from pydantic-ai message history."""

from pydantic_ai.messages import ModelMessage, ModelResponse

from scripts.common.run_outputs import TurnUsage


def extract_turn_usage(messages: list[ModelMessage]) -> list[TurnUsage]:
    """Extract per-turn usage by walking ModelResponse messages in order."""
    turns: list[TurnUsage] = []
    cumulative_input = 0
    cumulative_output = 0
    cumulative_total = 0

    for message in messages:
        if not isinstance(message, ModelResponse):
            continue

        usage = message.usage
        input_tokens = getattr(usage, "input_tokens", 0)
        output_tokens = getattr(usage, "output_tokens", 0)
        cache_write_tokens = getattr(usage, "cache_write_tokens", 0)
        cache_read_tokens = getattr(usage, "cache_read_tokens", 0)
        total_tokens = getattr(usage, "total_tokens", input_tokens + output_tokens)

        cumulative_input += input_tokens
        cumulative_output += output_tokens
        cumulative_total += total_tokens
        turns.append(
            TurnUsage(
                turn=len(turns) + 1,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_write_tokens=cache_write_tokens,
                cache_read_tokens=cache_read_tokens,
                total_tokens=total_tokens,
                cumulative_input_tokens=cumulative_input,
                cumulative_output_tokens=cumulative_output,
                cumulative_total_tokens=cumulative_total,
            )
        )

    return turns
