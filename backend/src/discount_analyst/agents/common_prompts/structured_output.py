"""Shared instructions for pydantic-ai tool-mode structured output."""

from discount_analyst.agents.runtime.structured_output_unwrap import (
    singleton_envelope_keys_for_prompt,
)

FINAL_RESULT_TOOL_NAME = "final_result"


def final_result_submit_section(*, output_type_name: str) -> str:
    """Prompt block: submit structured output only via ``final_result``."""
    envelope_keys = singleton_envelope_keys_for_prompt()
    return f"""
### Submit via {FINAL_RESULT_TOOL_NAME}

When your work is complete, call `{FINAL_RESULT_TOOL_NAME}` once with the completed `{output_type_name}` object. Pass schema fields as top-level `{FINAL_RESULT_TOOL_NAME}` arguments; do not nest them under {envelope_keys}. This is the **only** permitted way to return structured output. Do not emit a JSON block in free text as a substitute.

| Role | Callable name |
| --- | --- |
| Structured output | `{FINAL_RESULT_TOOL_NAME}` |
""".strip()


def final_result_user_step(*, output_type_name: str) -> str:
    """Short user-prompt reminder for the closing step."""
    return (
        f"Final step: call `{FINAL_RESULT_TOOL_NAME}` once with your completed "
        f"`{output_type_name}` object. Do not return JSON in free text."
    )
