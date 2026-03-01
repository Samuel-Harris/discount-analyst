#!/bin/bash
# sessionStart hook — injects branch and uv environment context
cat > /dev/null  # consume stdin

BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
VENV=$(uv run python -c "import sys; print(sys.prefix)" 2>/dev/null || echo "not found")

cat <<EOF
{
  "additional_context": "Git branch: $BRANCH. Python environment: uv venv at $VENV. Always prefix python/pytest/ruff commands with 'uv run'."
}
EOF
