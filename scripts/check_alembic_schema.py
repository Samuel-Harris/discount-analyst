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
    default_db = Path(tempfile.gettempdir()) / "discount-analyst-alembic-check.sqlite"
    db_path = Path(os.environ.get("DASHBOARD_DATABASE_PATH", str(default_db)))
    env = {**os.environ, "DASHBOARD_DATABASE_PATH": str(db_path)}

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
