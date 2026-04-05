"""Paths and model sets shared by scripts."""

from pathlib import Path

from discount_analyst.config.ai_models_config import ModelName

SCRIPTS_OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"

# Models that auto-cache (OpenAI, Gemini); no way to disable — skip when --caching disabled.
AUTO_CACHE_MODELS: frozenset[ModelName] = frozenset(
    {
        ModelName.GPT_5_1,
        ModelName.GPT_5_2,
        ModelName.GPT_5_4,
        ModelName.GEMINI_3_PRO_PREVIEW,
        ModelName.GEMINI_3_1_PRO_PREVIEW,
    }
)
