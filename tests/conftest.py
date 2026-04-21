"""Suite-wide pytest defaults (loaded before any test package under ``tests/``)."""

from __future__ import annotations

import os

# Minimal defaults so ``common.config.settings`` can import during tests
# (integration tests override via ``dashboard_settings_for_tests`` where needed).
os.environ.setdefault("LOGGING__LOGFIRE_API_KEY", "pytest-dummy-logfire-token")
os.environ.setdefault("PERPLEXITY__API_KEY", "pytest-dummy-perplexity")
os.environ.setdefault("PERPLEXITY__RATE_LIMIT_PER_MINUTE", "60")
os.environ.setdefault("FMP__API_KEY", "pytest-dummy-fmp")
os.environ.setdefault("EODHD__API_KEY", "pytest-dummy-eodhd")
