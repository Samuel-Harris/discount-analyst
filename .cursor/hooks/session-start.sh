#!/bin/bash
# sessionStart hook — injects branch and Poetry environment context
cat > /dev/null  # consume stdin

BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
VENV=$(poetry env list --full-path 2>/dev/null | head -1 | awk '{print $1}' || echo "not found")

cat <<EOF
{
  "additional_context": "Git branch: $BRANCH. Python environment: Poetry venv at $VENV. Always prefix python/pytest/ruff commands with 'poetry run'."
}
EOF
