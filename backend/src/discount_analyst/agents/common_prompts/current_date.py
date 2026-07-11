"""Shared current-date context for agent system prompts."""

from datetime import date


def format_current_date_line(*, when: date | None = None) -> str:
    """Return a single line stating today's date (ISO 8601)."""
    today = when or date.today()
    return f"Today's date is {today.isoformat()}."


def with_current_date(system_prompt: str, *, when: date | None = None) -> str:
    """Prepend today's date to a base agent system prompt."""
    date_line = format_current_date_line(when=when)
    base = system_prompt.strip()
    if not base:
        return date_line
    return f"{date_line}\n\n{base}"
