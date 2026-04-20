"""Test-only dashboard settings helpers (not used by the running API)."""

from pydantic import SecretStr

# Satisfies ``DashboardSettings`` validation when constructing settings explicitly in tests.
LOGFIRE_TOKEN_FOR_TESTS = SecretStr("pytest-dummy-logfire-token")
