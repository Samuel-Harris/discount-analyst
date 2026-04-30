"""Programmatic Alembic migration entry-point for dashboard startup."""

from __future__ import annotations

from pathlib import Path

import logfire
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Connection

from backend.observability.db_url import redact_database_url_for_log


def _alembic_config(database_url: str) -> Config:
    db_dir = Path(__file__).resolve().parent
    cfg = Config(str(db_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(db_dir / "alembic"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def migrate_to_head(database_url: str, *, connection: Connection | None = None) -> None:
    safe_url = redact_database_url_for_log(database_url)
    logfire.debug("Alembic upgrade to head starting", database_url=safe_url)
    cfg = _alembic_config(database_url)
    if connection is not None:
        cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")
    logfire.info("Alembic upgrade to head completed", database_url=safe_url)
