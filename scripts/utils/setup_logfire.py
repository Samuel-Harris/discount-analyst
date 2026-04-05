import logfire

from discount_analyst.config.settings import settings


def setup_logfire() -> None:
    logfire.configure(token=settings.pydantic.logfire_api_key)
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)
