"""Tests for Surveyor output validation."""

import pytest
from pydantic import ValidationError

from discount_analyst.adapters.simulation.mock_outputs import mock_surveyor_candidate
from discount_analyst.agents.surveyor.schema import SurveyorCandidate, SurveyorOutput


def _candidate(ticker: str) -> SurveyorCandidate:
    return mock_surveyor_candidate(ticker=ticker)


def _fifteen_unique_candidates() -> list[SurveyorCandidate]:
    return [_candidate(f"TST{i:02d}.L") for i in range(15)]


def test_surveyor_output_accepts_unique_candidate_tickers() -> None:
    output = SurveyorOutput(candidates=_fifteen_unique_candidates())

    assert len(output.candidates) == 15


def test_surveyor_output_rejects_duplicate_candidate_tickers_case_insensitive() -> None:
    candidates = _fifteen_unique_candidates()
    candidates[-1] = _candidate("tst00.l")

    with pytest.raises(ValidationError, match="Duplicate Surveyor candidate ticker"):
        SurveyorOutput(candidates=candidates)


def test_surveyor_output_rejects_duplicate_candidate_tickers_after_trimming() -> None:
    candidates = _fifteen_unique_candidates()
    candidates[-1] = _candidate(" TST00.L ")

    with pytest.raises(ValidationError, match="Duplicate Surveyor candidate ticker"):
        SurveyorOutput(candidates=candidates)
