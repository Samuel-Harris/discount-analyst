"""HTTP-facing string enums and mapping to ``discount_analyst.agents.runtime.agent_names.AgentName``."""

from enum import StrEnum


class WorkflowRunStatusApi(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TickerRunStatusApi(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStatusApi(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EntryPathApi(StrEnum):
    SURVEYOR = "surveyor"
    PROFILER = "profiler"


class DecisionTypeApi(StrEnum):
    RATING_TABLE = "rating_table"
    SENTINEL_REJECTION = "sentinel_rejection"
    DATA_QUALITY_REJECTION = "data_quality_rejection"


class CandidateGateStatusApi(StrEnum):
    PASSED = "passed"
    REJECTED = "rejected"


class AgentNameSlug(StrEnum):
    SURVEYOR = "surveyor"
    PROFILER = "profiler"
    RESEARCHER = "researcher"
    STRATEGIST = "strategist"
    SENTINEL = "sentinel"
    APPRAISER = "appraiser"
