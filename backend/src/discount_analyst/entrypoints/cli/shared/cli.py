"""Argparse helpers for scripts/agents entry points."""

import argparse
from dataclasses import dataclass

from discount_analyst.config.settings import settings
from discount_analyst.agents.runtime.terminal_run import (
    TerminalRunOptions,
    terminal_run_options,
)
from discount_analyst.domain.model_selection.model_name import ModelName


@dataclass(frozen=True, slots=True)
class AgentCliDefaults:
    """Default model and web-search backend for `scripts/agents/` entry points."""

    model: ModelName
    use_perplexity: bool


DEFAULT_AGENT_CLI_DEFAULTS = AgentCliDefaults(
    model=ModelName.DEEPSEEK_V4_PRO,
    use_perplexity=False,
)


def add_agent_cli_model_argument(
    parser: argparse.ArgumentParser,
    *,
    default_override: AgentCliDefaults | None = None,
) -> None:
    """Register ``--model`` using shared agent CLI defaults."""
    resolved_defaults = default_override or DEFAULT_AGENT_CLI_DEFAULTS
    parser.add_argument(
        "--model",
        type=ModelName,
        choices=[e.value for e in ModelName],
        default=resolved_defaults.model,
        help=f"AI model to use (default: {resolved_defaults.model})",
    )


def add_agent_terminal_argument(parser: argparse.ArgumentParser) -> None:
    """Register ``--no-terminal`` (namespace attribute: ``no_terminal``)."""
    parser.add_argument(
        "--no-terminal",
        action="store_true",
        help="Do not register the docker-backed terminal_exec tool for this run.",
    )


def terminal_run_options_for_cli(*, no_terminal: bool) -> TerminalRunOptions:
    """Build :class:`TerminalRunOptions` from process settings and CLI flags."""
    return terminal_run_options(settings, enabled=not no_terminal)


def add_agent_cli_web_search_arguments(
    parser: argparse.ArgumentParser,
    *,
    default_override: AgentCliDefaults | None = None,
) -> None:
    """Register optional ``--perplexity`` (default: Pydantic AI web capabilities).

    Namespace attribute: ``use_perplexity``.
    """
    resolved_defaults = default_override or DEFAULT_AGENT_CLI_DEFAULTS
    parser.set_defaults(use_perplexity=resolved_defaults.use_perplexity)
    parser.add_argument(
        "--perplexity",
        action="store_true",
        dest="use_perplexity",
        help=(
            "Use Perplexity API for web_search and sec_filings_search "
            "(default: Pydantic AI WebSearch/WebFetch)."
        ),
    )
