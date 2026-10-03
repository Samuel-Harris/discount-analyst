"""Shared Logfire tagging for AI observability."""

import logfire
from logfire import Logfire

AI_LOG_TAG = "ai"
AI_LOGFIRE: Logfire = logfire.with_tags(AI_LOG_TAG)
