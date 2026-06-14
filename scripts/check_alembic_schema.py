#!/usr/bin/env python3
"""Verify Alembic head matches SQLModel metadata and a single revision head exists."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = REPO_ROOT / "backend" / "db" / "alembic.ini"

# Alembic env.py imports backend.db.session → common.config.settings at load time.
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


def _alembic_subprocess_env() -> dict[str, str]:
    env = {**os.environ}
    for key, value in _ALEMBIC_SETTINGS_DEFAULTS.items():
        env.setdefault(key, value)
    default_db = Path(tempfile.gettempdir()) / "discount-analyst-alembic-check.sqlite"
    env.setdefault("DASHBOARD_DATABASE_PATH", str(default_db))
    return env


def _run(cmd: list[str], *, env: dict[str, str]) -> None:
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)


def main() -> int:
    env = _alembic_subprocess_env()

    alembic = ["uv", "run", "alembic", "-c", str(ALEMBIC_INI)]
    _run([*alembic, "upgrade", "head"], env=env)
    _run([*alembic, "check"], env=env)

    heads = subprocess.run(
        [*alembic, "heads"],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    head_lines = [line for line in heads.stdout.splitlines() if line.strip()]
    if len(head_lines) != 1:
        print(
            f"Expected exactly one Alembic head, found {len(head_lines)}:",
            file=sys.stderr,
        )
        for line in head_lines:
            print(line, file=sys.stderr)
        return 1

    print("Alembic schema matches ORM metadata at head.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
