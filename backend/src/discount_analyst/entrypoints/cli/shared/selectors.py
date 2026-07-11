"""Shared CLI selectors for upstream agent JSON artefacts."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Selector:
    report_path: Path
    ticker: str | None
    raw: str


def parse_report_selector(
    raw: str,
    parser: argparse.ArgumentParser,
    *,
    flag_name: str,
    artefact_label: str,
) -> Selector:
    """Parse ``path`` or ``path:TICKER`` selectors for agent CLI entry points."""
    example = f"<{artefact_label.lower()}_run_output.json>"
    example_with_ticker = f"{example}:<TICKER>"
    stripped = raw.strip()
    if not stripped:
        parser.error(
            f"Invalid {flag_name} value: empty selector. "
            f"Expected '{example}' or '{example_with_ticker}'."
        )

    report_part: str
    ticker_part: str | None
    if ":" in stripped:
        report_part, ticker_part = stripped.rsplit(":", maxsplit=1)
        report_part = report_part.strip()
        ticker_part = ticker_part.strip()
        if not report_part or not ticker_part:
            parser.error(
                f"Invalid selector '{raw}'. Expected "
                f"'{example}' or '{example_with_ticker}'."
            )
    else:
        report_part = stripped
        ticker_part = None

    path = Path(report_part).expanduser().resolve()
    if path.suffix.lower() != ".json":
        parser.error(
            f"Invalid selector '{raw}': expected a .json {artefact_label} run "
            f"artefact path. Got: {path}."
        )
    if not path.is_file():
        parser.error(
            f"Invalid selector '{raw}': {artefact_label} output file not found at "
            f"{path}. Expected '{example}' or '{example_with_ticker}'."
        )

    return Selector(report_path=path, ticker=ticker_part, raw=raw)
