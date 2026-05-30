"""Context propagation for per-agent-run terminal sandbox sessions."""

from contextvars import ContextVar, Token

_terminal_session_id: ContextVar[str | None] = ContextVar(
    "discount_analyst_terminal_session_id", default=None
)


def get_terminal_session_id() -> str | None:
    """Return the active terminal session id for this async context, if any."""
    return _terminal_session_id.get()


def set_terminal_session_id(session_id: str) -> Token[str | None]:
    """Bind ``session_id`` for downstream ``terminal_exec`` tool calls."""
    return _terminal_session_id.set(session_id)


def reset_terminal_session_id(token: Token[str | None]) -> None:
    """Restore the previous terminal session id (typically after an agent run)."""
    _terminal_session_id.reset(token)
