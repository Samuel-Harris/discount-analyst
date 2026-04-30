"""Argparse helpers for scripts/agents entry points."""

import argparse
from dataclasses import dataclass

from discount_analyst.config.ai_models_config import ModelName


@dataclass(frozen=True, slots=True)
class AgentCliDefaults:
    """Default model and web-search backend for `scripts/agents/` entry points."""

    model: ModelName
    use_perplexity: bool


DEFAULT_AGENT_CLI_DEFAULTS = AgentCliDefaults(
    model=ModelName.GPT_5_1,
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


def add_agent_cli_web_search_arguments(
    parser: argparse.ArgumentParser,
    *,
    default_override: AgentCliDefaults | None = None,
) -> None:
    """Register optional ``--perplexity`` (default: model-native web search).

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
            "(default: model-native web search)."
        ),
    )
