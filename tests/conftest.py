"""Suite-wide pytest defaults (loaded before any test package under ``tests/``)."""

from __future__ import annotations

import os

# Dashboard API requires ``DASHBOARD_LOGFIRE_TOKEN``; tests use a dummy unless overridden.
os.environ.setdefault("DASHBOARD_LOGFIRE_TOKEN", "pytest-dummy-logfire-token")
