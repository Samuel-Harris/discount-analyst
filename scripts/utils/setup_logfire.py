import logfire

from discount_analyst.shared.config.settings import settings


def setup_logfire() -> None:
    """Configure Logfire and attach a session ID to all spans.

    Args:
        session_id: Optional session ID. If None, uses LOGFIRE_SESSION_ID env var,
            or auto-generates a UUID. All spans in this process will have the
            session_id resource attribute for grouping in the Logfire UI.
    """

    logfire.configure(token=settings.pydantic.logfire_api_key)
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)
