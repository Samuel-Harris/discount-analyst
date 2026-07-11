#!/usr/bin/env python3
"""Verify Alembic head matches SQLModel metadata and a single revision head exists."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Alembic env.py imports persistence.session → composition.settings at load time.
# Supply minimal defaults when unset (same keys as tests/conftest.py).
_ALEMBIC_SETTINGS_DEFAULTS: dict[str, str] = {
    "LOGGING__LOGFIRE_API_KEY": "pytest-dummy-logfire-token",
    "OPENAI__API_KEY": "pytest-dummy-openai",
    "DEEPSEEK__API_KEY": "pytest-dummy-deepseek",
    "PERPLEXITY__API_KEY": "pytest-dummy-perplexity",
    "PERPLEXITY__RATE_LIMIT_PER_MINUTE": "60",
    "FMP__API_KEY": "pytest-dummy-fmp",
    "EODHD__API_KEY": "pytest-dummy-eodhd",
    "DASHBOARD_USE_TERMINAL": "false",
}


def _apply_env_defaults() -> Path:
    for key, value in _ALEMBIC_SETTINGS_DEFAULTS.items():
        os.environ.setdefault(key, value)
    default_db = Path(tempfile.gettempdir()) / "discount-analyst-alembic-check.sqlite"
    db_path = Path(os.environ.get("DASHBOARD_DATABASE_PATH", str(default_db)))
    os.environ.setdefault("DASHBOARD_DATABASE_PATH", str(db_path))
    return db_path


def main() -> int:
    db_path = _apply_env_defaults()
    from discount_analyst.adapters.persistence.session import sqlite_url_from_path
    from discount_analyst.adapters.persistence.verify_schema import (
        AlembicSchemaError,
        verify_alembic_schema,
    )

    try:
        verify_alembic_schema(database_url=sqlite_url_from_path(db_path))
    except AlembicSchemaError as exc:
        print(exc, file=sys.stderr)
        return 1

    print("Alembic schema matches ORM metadata at head.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
