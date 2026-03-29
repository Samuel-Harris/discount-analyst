from __future__ import annotations

from collections.abc import Callable

from pydantic_ai import RunContext
from pydantic_ai.messages import ModelMessage

from discount_analyst.shared.config.ai_models_config import ModelName

type HistoryProcessor = Callable[
    [RunContext[None], list[ModelMessage]], list[ModelMessage]
]


def get_history_processors_for_model(model_name: ModelName) -> list[HistoryProcessor]:
    """Return model-specific history processors.

    Local transcript compaction is intentionally disabled. OpenAI models use
    official server-side compaction via model settings, and other providers
    currently run without local slicing.
    """
    _ = model_name
    return []
