"""Architecture contracts enforced by import-linter."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_import_linter_contracts() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "importlinter.cli", "lint-imports"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"import-linter failed:\n{result.stdout}\n{result.stderr}")


def test_tach_check_external() -> None:
    """Declared pyproject.toml dependencies must match third-party imports."""
    result = subprocess.run(
        [sys.executable, "-m", "tach", "check-external"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"tach check-external failed:\n{result.stdout}\n{result.stderr}")


def test_agent_terminal_not_imported_by_monolith() -> None:
    """Monolith must talk to agent-terminal only over HTTP (no Python imports)."""
    src = REPO_ROOT / "backend" / "src" / "discount_analyst"
    offenders: list[str] = []
    for path in src.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            module: str | None = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module
            if module is None:
                continue
            if module == "agent_terminal" or module.startswith(
                ("agent_terminal.", "services.agent_terminal")
            ):
                offenders.append(str(path.relative_to(REPO_ROOT)))
                break
    assert not offenders, f"Monolith must not import agent-terminal: {offenders}"
