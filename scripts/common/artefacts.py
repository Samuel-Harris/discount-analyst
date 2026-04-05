"""Write script run JSON artefacts and build output filenames."""

import re
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, TypeAdapter

from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.config.ai_models_config import ModelName
from discount_analyst.pipeline.schema import Verdict

from scripts.common.constants import SCRIPTS_OUTPUTS_DIR


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


def write_verdicts_json(*, verdicts: list[Verdict], model_name: ModelName) -> Path:
    """Serialise ``list[Verdict]`` to ``scripts/outputs``; stem includes ``VERDICTS``."""
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    safe_model = model_name.value.replace(".", "-")
    filename = f"{ts}-{safe_model}-VERDICTS.json"
    SCRIPTS_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    path = SCRIPTS_OUTPUTS_DIR / filename
    adapter = TypeAdapter(list[Verdict])
    path.write_text(adapter.dump_json(verdicts, indent=2, exclude_none=False).decode())
    return path.resolve()
