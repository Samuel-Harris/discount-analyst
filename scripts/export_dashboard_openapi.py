"""Write the dashboard FastAPI OpenAPI schema for frontend code generation (Orval).

Run from the repository root::

    uv run python scripts/export_dashboard_openapi.py

For an isolated database (CI or one-off export), set ``DASHBOARD_DATABASE_PATH`` to a
throwaway file path before running.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.main import create_app


def _default_output_path() -> Path:
    return Path(__file__).resolve().parent.parent / "frontend" / "openapi.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=_default_output_path(),
        help="Path to write openapi.json (default: frontend/openapi.json under repo root)",
    )
    args = parser.parse_args()
    output: Path = args.output

    app = create_app()
    schema = app.openapi()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
