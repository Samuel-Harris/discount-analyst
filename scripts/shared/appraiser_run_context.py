"""CLI/workflow metadata for a single Appraiser run."""

from __future__ import annotations

from dataclasses import dataclass

from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.models.model_name import ModelName


@dataclass(frozen=True)
class AppraiserRunContext:
    """CLI/workflow metadata for a single Appraiser run (model + RFR + candidate)."""

    surveyor_candidate: SurveyorCandidate
    risk_free_rate_pct: float
    model: ModelName
