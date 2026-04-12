"""Programmatic Alembic migration entry-point for dashboard startup."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Connection


def _alembic_config(database_url: str) -> Config:
    db_dir = Path(__file__).resolve().parent
    cfg = Config(str(db_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(db_dir / "alembic"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def migrate_to_head(database_url: str, *, connection: Connection | None = None) -> None:
    cfg = _alembic_config(database_url)
    if connection is not None:
        cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")
