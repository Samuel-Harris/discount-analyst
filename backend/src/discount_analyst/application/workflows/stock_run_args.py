"""Shared pipeline inputs for Appraiser-stage DCF (dashboard + CLI)."""

from __future__ import annotations

from dataclasses import dataclass

from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.domain.model_selection.model_name import ModelName


@dataclass
class StockRunArgs:
    surveyor_candidate: SurveyorCandidate
    risk_free_rate_pct: float
    model: ModelName
