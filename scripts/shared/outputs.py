"""Write script run JSON artifacts and build output filenames."""

import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from discount_analyst.shared.config.ai_models_config import ModelName
from discount_analyst.shared.constants.agents import AgentName

from scripts.shared.constants import SCRIPTS_OUTPUTS_DIR
from scripts.shared.schemas.run_outputs import AppraiserRunOutput


def _sanitize_filename_suffix_body(s: str) -> str:
    """Allow [A-Za-z0-9._-] only; other chars become '-'; collapse and trim hyphens."""
    stripped = s.strip()
    if not stripped:
        return ""
    chars: list[str] = []
    for c in stripped:
        if c in "._-" or ("A" <= c <= "Z") or ("a" <= c <= "z") or ("0" <= c <= "9"):
            chars.append(c)
        else:
            chars.append("-")
    collapsed = re.sub(r"-+", "-", "".join(chars)).strip("-")
    return collapsed


def write_agent_json(
    *,
    payload: BaseModel,
    model_name: ModelName,
    agent_name: AgentName,
    filename_suffix: str | None = None,
) -> Path:
    """Serialise a Pydantic payload to ``scripts/outputs/`` and return the path written.

    Filename stem: ``{timestamp}-{model}-{AGENT}{optional_suffix}.json`` with
    ``timestamp`` as ``YYYY-mm-dd-HH-MM-SS`` and model dots replaced by hyphens.
    """
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    safe_model = model_name.value.replace(".", "-")
    if filename_suffix is None or not filename_suffix.strip():
        suffix = ""
    else:
        body = _sanitize_filename_suffix_body(filename_suffix)
        suffix = "" if body == "" else (body if body.startswith("-") else f"-{body}")
    filename = f"{ts}-{safe_model}-{agent_name.value}{suffix}.json"
    SCRIPTS_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    path = SCRIPTS_OUTPUTS_DIR / filename
    path.write_text(payload.model_dump_json(indent=2))
    return path.resolve()


def output_filename(
    timestamp: str,
    model_name: str,
    ticker: str,
    cache_enabled: bool,
    use_web_search: bool = False,
) -> str:
    """Return output filename for a run (same pattern as write_model_output)."""
    safe_model = model_name.replace(".", "-")
    cache_part = "cache" if cache_enabled else "no-cache"
    search_part = "web-search" if use_web_search else "perplexity"
    return f"{timestamp}-{safe_model}-{cache_part}-{search_part}-{ticker}.json"


def write_model_output(
    *,
    run_output: AppraiserRunOutput,
    timestamp: str,
    output_dir: Path,
    cache_suffix: Literal["cache", "no-cache"] | None = None,
    search_suffix: Literal["web-search", "perplexity"] | None = None,
) -> Path:
    """Serialise the full run output (agent + DCF) to JSON and return the path written.

    When cache_suffix and search_suffix are omitted, the filename is
    {timestamp}-{model}-{ticker}.json. When set, they are included before the ticker.
    """
    safe_model = run_output.model_name.replace(".", "-")
    parts: list[str] = [timestamp, safe_model]
    if cache_suffix is not None:
        parts.append(cache_suffix)
    if search_suffix is not None:
        parts.append(search_suffix)
    parts.append(run_output.ticker)
    filename = "-".join(parts) + ".json"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_text(run_output.model_dump_json(indent=2))
    return path
