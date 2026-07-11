"""Verify Alembic migration head matches SQLModel ORM metadata."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

# adapters/persistence → … → backend/
_BACKEND_ROOT = Path(__file__).resolve().parents[4]
ALEMBIC_INI = _BACKEND_ROOT / "migrations" / "alembic.ini"
ALEMBIC_SCRIPT_DIR = _BACKEND_ROOT / "migrations"


class AlembicSchemaError(RuntimeError):
    """Raised when Alembic head count or metadata check fails."""


def alembic_config_for_url(database_url: str) -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(ALEMBIC_SCRIPT_DIR))
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def verify_alembic_head_matches_metadata(*, database_url: str) -> None:
    """Upgrade to head and assert ORM metadata matches applied migrations."""
    cfg = alembic_config_for_url(database_url)
    command.upgrade(cfg, "head")
    command.check(cfg)


def verify_single_alembic_head(*, database_url: str) -> None:
    """Assert exactly one Alembic revision head exists."""
    cfg = alembic_config_for_url(database_url)
    heads = ScriptDirectory.from_config(cfg).get_heads()
    if len(heads) != 1:
        lines = "\n".join(heads) if heads else "(none)"
        raise AlembicSchemaError(
            f"Expected exactly one Alembic head, found {len(heads)}:\n{lines}"
        )


def verify_alembic_schema(*, database_url: str) -> None:
    """Run metadata check and single-head validation."""
    verify_alembic_head_matches_metadata(database_url=database_url)
    verify_single_alembic_head(database_url=database_url)
