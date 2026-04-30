"""Shared AI-tagged Logfire helper utilities."""

from __future__ import annotations

import logfire
from logfire import Logfire

from discount_analyst.agents.common.logging_constants import AI_LOG_TAG

AI_LOGFIRE: Logfire = logfire.with_tags(AI_LOG_TAG)
