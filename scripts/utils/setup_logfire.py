import logfire

from discount_analyst.shared.config.settings import settings


def setup_logfire() -> None:
    """Configure Logfire and attach a session ID to all spans."""

    logfire.configure(token=settings.pydantic.logfire_api_key)
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)
