#!/bin/bash
# afterFileEdit hook — auto-formats and lints edited Python files with ruff
FILE=$(python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null)

if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
  exit 0
fi

uv run ruff check --fix --quiet "$FILE" 2>/dev/null || true
uv run ruff format --quiet "$FILE" 2>/dev/null || true
