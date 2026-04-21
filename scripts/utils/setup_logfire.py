import logfire

from discount_analyst.agents.common.ai_logging import AI_LOGFIRE
from discount_analyst.config.settings import settings


def setup_logfire() -> None:
    logfire.configure(token=settings.logging.logfire_api_key)
    AI_LOGFIRE.instrument_pydantic_ai()
    AI_LOGFIRE.instrument_httpx(capture_all=True)
