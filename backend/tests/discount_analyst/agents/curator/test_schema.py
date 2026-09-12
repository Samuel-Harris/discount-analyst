"""Tests for compact Curator evidence and proposal contracts."""

from datetime import date

import pytest
from pydantic import ValidationError

from discount_analyst.agents.curator.schema import (
    AppraisedLaneEvidence,
    CuratorLaneIdentity,
    CuratorProposal,
    CompactAppraiserEvidence,
    CompactResearcherEvidence,
    CompactSentinelEvidence,
    CompactStrategistEvidence,
    PackedMispricingThesis,
    ProposedCash,
    ProposedPosition,
    ProposedSharedRiskCluster,
)


def _identity(
    *,
    ticker: str = "ABC.L",
    is_existing: bool = False,
    weight: float = 0.0,
) -> CuratorLaneIdentity:
    return CuratorLaneIdentity(
        ticker=ticker,
        company_name="Abc plc",
        is_existing_position=is_existing,
        current_weight_pct=weight,
        sector="Technology",
        industry="Semiconductors",
    )


def _packed_thesis(*, ticker: str = "ABC.L") -> PackedMispricingThesis:
    return PackedMispricingThesis(
        ticker=ticker,
        company_name="Abc plc",
        mispricing_type="Cyclical trough",
        market_belief="The market believes decline is structural.",
        mispricing_argument="The trough is cyclical.",
        resolution_mechanism="Earnings normalisation.",
        falsification_conditions=["C1", "C2", "C3"],
        thesis_risks=["Risk"],
        evaluation_questions=["Q1", "Q2", "Q3", "Q4", "Q5"],
        permanent_loss_scenarios=["Loss"],
        conviction_level="Medium",
    )


def _appraised_lane(*, ticker: str = "ABC.L") -> AppraisedLaneEvidence:
    return AppraisedLaneEvidence(
        identity=_identity(ticker=ticker),
        live_thesis=_packed_thesis(ticker=ticker),
        researcher=CompactResearcherEvidence(
            customer_segments="Enterprise",
            risks=("Competition",),
        ),
        strategist=CompactStrategistEvidence(
            thesis_summary="The trough is cyclical.",
            conviction="Medium",
            thesis_risks=("Risk",),
            permanent_loss_scenarios=("Loss",),
        ),
        sentinel=CompactSentinelEvidence(
            customer_or_supplier_concentration="Diversified",
            red_flag_verdict="Clear",
            thesis_verdict="Thesis intact — proceed to valuation",
            material_data_gaps="None",
        ),
        appraiser=CompactAppraiserEvidence(
            current_price=10.0,
            expected_value=14.0,
            p10=8.0,
            p90=20.0,
            margin_of_safety_base_pct=40.0,
            data_quality="High",
        ),
    )


def test_appraised_lane_has_no_policy_or_rating() -> None:
    dumped = _appraised_lane().model_dump()
    assert "decision_kind" not in dumped
    assert "policy" not in dumped["identity"]
    assert "rating" not in dumped["identity"]


def test_proposal_rejects_unordered_range() -> None:
    with pytest.raises(ValidationError, match="0 <= low <= target <= high"):
        CuratorProposal(
            allocation_date=date(2026, 8, 30),
            positions=(
                ProposedPosition(
                    ticker="ABC.L",
                    target_weight_pct=10.0,
                    acceptable_weight_low_pct=12.0,
                    acceptable_weight_high_pct=14.0,
                    rationale="Bad range.",
                ),
            ),
            cash=ProposedCash(
                target_weight_pct=90.0,
                acceptable_weight_low_pct=80.0,
                acceptable_weight_high_pct=100.0,
                rationale="Cash.",
            ),
            shared_risk_clusters=(),
            portfolio_rationale="Invalid.",
        )


def test_proposal_requires_unique_tickers() -> None:
    with pytest.raises(ValidationError, match="unique"):
        CuratorProposal(
            allocation_date=date(2026, 8, 30),
            positions=(
                ProposedPosition(
                    ticker="ABC.L",
                    target_weight_pct=10.0,
                    acceptable_weight_low_pct=8.0,
                    acceptable_weight_high_pct=12.0,
                    rationale="One.",
                ),
                ProposedPosition(
                    ticker="abc.l",
                    target_weight_pct=10.0,
                    acceptable_weight_low_pct=8.0,
                    acceptable_weight_high_pct=12.0,
                    rationale="Two.",
                ),
            ),
            cash=ProposedCash(
                target_weight_pct=80.0,
                acceptable_weight_low_pct=70.0,
                acceptable_weight_high_pct=90.0,
                rationale="Cash.",
            ),
            shared_risk_clusters=(),
            portfolio_rationale="Dupes.",
        )


def test_proposal_rejects_targets_not_totalling_100() -> None:
    with pytest.raises(ValidationError, match="total 100%"):
        CuratorProposal(
            allocation_date=date(2026, 8, 30),
            positions=(
                ProposedPosition(
                    ticker="ABC.L",
                    target_weight_pct=40.0,
                    acceptable_weight_low_pct=30.0,
                    acceptable_weight_high_pct=50.0,
                    rationale="Too large.",
                ),
            ),
            cash=ProposedCash(
                target_weight_pct=40.0,
                acceptable_weight_low_pct=30.0,
                acceptable_weight_high_pct=50.0,
                rationale="Cash.",
            ),
            shared_risk_clusters=(),
            portfolio_rationale="Test.",
        )


def test_proposal_rejects_single_ticker_cluster() -> None:
    with pytest.raises(ValidationError, match="at least two"):
        CuratorProposal(
            allocation_date=date(2026, 8, 30),
            positions=(),
            cash=ProposedCash(
                target_weight_pct=100.0,
                acceptable_weight_low_pct=100.0,
                acceptable_weight_high_pct=100.0,
                rationale="All cash.",
            ),
            shared_risk_clusters=(
                ProposedSharedRiskCluster(
                    label="Lonely",
                    member_tickers=("ABC.L",),
                    mechanism="None",
                    allocation_effect="None",
                ),
            ),
            portfolio_rationale="Test.",
        )


def test_cash_only_proposal_is_valid() -> None:
    proposal = CuratorProposal(
        allocation_date=date(2026, 8, 30),
        positions=(),
        cash=ProposedCash(
            target_weight_pct=100.0,
            acceptable_weight_low_pct=100.0,
            acceptable_weight_high_pct=100.0,
            rationale="Empty universe.",
        ),
        shared_risk_clusters=(),
        portfolio_rationale="Cash only.",
    )

    assert proposal.cash.target_weight_pct == 100.0
