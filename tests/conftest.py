"""Suite-wide pytest defaults (loaded before any test package under ``tests/``)."""

from __future__ import annotations

import os

# Ensure tests use a stable Logfire token unless the environment already sets one.
os.environ.setdefault("DASHBOARD_LOGFIRE_TOKEN", "pytest-dummy-logfire-token")
