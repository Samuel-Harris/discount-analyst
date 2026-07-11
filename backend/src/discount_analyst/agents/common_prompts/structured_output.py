"""Shared instructions for pydantic-ai tool-mode structured output."""

FINAL_RESULT_TOOL_NAME = "final_result"


def final_result_submit_section(*, output_type_name: str) -> str:
    """Prompt block: submit structured output only via ``final_result``."""
    return f"""
### Submit via {FINAL_RESULT_TOOL_NAME}

When your work is complete, call `{FINAL_RESULT_TOOL_NAME}` once with the completed `{output_type_name}` object. This is the **only** permitted way to return structured output. Do not emit a JSON block in free text as a substitute.

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
