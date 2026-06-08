from datetime import date

from discount_analyst.agents.common_prompts.current_date import (
    format_current_date_line,
    with_current_date,
)


def test_format_current_date_line_uses_iso_format() -> None:
    assert format_current_date_line(when=date(2026, 6, 8)) == "Today's date is 2026-06-08."


def test_with_current_date_prepends_line_before_base_prompt() -> None:
    result = with_current_date("Base prompt.", when=date(2026, 6, 8))
    assert result == "Today's date is 2026-06-08.\n\nBase prompt."


def test_with_current_date_returns_only_date_line_for_empty_base() -> None:
    assert with_current_date("", when=date(2026, 6, 8)) == "Today's date is 2026-06-08."
    assert with_current_date("   ", when=date(2026, 6, 8)) == "Today's date is 2026-06-08."
