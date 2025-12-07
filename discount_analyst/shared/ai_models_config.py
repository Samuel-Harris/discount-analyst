from pydantic import BaseModel


class AIModelsConfig(BaseModel):
    """Configuration for AI model names used by different components."""

    assumption_maker_provider: str = "anthropic"
    assumption_maker_model: str = "claude-opus-4-5-20251101"


ai_models_config = AIModelsConfig()
