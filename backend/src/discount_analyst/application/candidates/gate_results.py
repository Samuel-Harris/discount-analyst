"""Candidate-gate result types shared by persistence and market-data."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from discount_analyst.agents.surveyor.schema import SurveyorLaneContext


type GateDataSource = Literal["fmp", "eodhd", "mock"]


class TickerResolution(BaseModel):
    source_ticker: str
    resolved_ticker: str
    resolution_notes: str
    data_source: GateDataSource


class ListingProbe(BaseModel):
    resolution_notes: str
    is_actively_trading: bool
    data_source: GateDataSource


class PassedCandidateGate(BaseModel):
    gate_status: Literal["passed"] = "passed"
    source_ticker: str
    resolved_ticker: str
    resolution_notes: str
    is_actively_trading: bool
    data_source: GateDataSource
    lane_context: SurveyorLaneContext


class RejectedCandidateGate(BaseModel):
    gate_status: Literal["rejected"] = "rejected"
    source_ticker: str
    resolved_ticker: str | None
    resolution_notes: str
    gate_failure_reason: str
    is_actively_trading: bool | None
    data_source: GateDataSource


type CandidateGateResult = PassedCandidateGate | RejectedCandidateGate
