#!/usr/bin/env sh
set -eu

if [ -n "${DASHBOARD_DATABASE_PATH:-}" ]; then
  mkdir -p "$(dirname "$DASHBOARD_DATABASE_PATH")"
fi

uv run alembic -c backend/db/alembic.ini upgrade head

exec uv run uvicorn backend.app.main:create_app --factory --host 0.0.0.0 --port 8000
