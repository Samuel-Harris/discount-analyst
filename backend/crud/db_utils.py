"""Shared helpers for CRUD modules (ids, timestamps, JSON, execution status sets)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from backend.db.models import ExecutionStatusDb

TERMINAL_EXECUTION_STATUSES = frozenset(
    {
        ExecutionStatusDb.COMPLETED.value,
        ExecutionStatusDb.SKIPPED.value,
        ExecutionStatusDb.REJECTED.value,
        ExecutionStatusDb.FAILED.value,
        ExecutionStatusDb.CANCELLED.value,
    }
)
ACTIVE_EXECUTION_STATUSES = frozenset(
    {
        ExecutionStatusDb.PENDING.value,
        ExecutionStatusDb.RUNNING.value,
    }
)


def new_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_iso() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def dump_json_string(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
