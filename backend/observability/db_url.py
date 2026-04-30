"""Safe database URL summaries for logs (no credentials or full paths)."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.engine.url import make_url


def redact_database_url_for_log(database_url: str) -> str:
    """Return a short, non-sensitive description of a SQLAlchemy database URL."""
    u = make_url(database_url)
    if u.drivername == "sqlite":
        if not u.database or u.database == ":memory:":
            return "sqlite:///:memory:"
        return f"sqlite:///{Path(u.database).name}"
    host = u.host or "unknown"
    return f"{u.drivername}://{host}/<redacted>"
