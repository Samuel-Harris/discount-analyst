"""Tests for compact Curator evidence and proposal contracts."""

from datetime import date

import pytest
from pydantic import ValidationError

from discount_analyst.agents.curator.schema import (
    CuratorLaneIdentity,
    CuratorProposal,
    CompactResearcherEvidence,
    CompactSentinelEvidence,
    CompactStrategistEvidence,
    DataQualityRejectionLaneEvidence,
    PackedMispricingThesis,
    ProposedCash,
    ProposedPosition,
    ProposedSharedRiskCluster,
    SentinelRejectionLaneEvidence,
)
from discount_analyst.domain.allocations.policy import (
    ForcedZeroPolicy,
    ForcedZeroReason,
    InvestablePolicy,
)
from discount_analyst.domain.decisions.investment_rating import InvestmentRating


def _identity(
    *,
    ticker: str = "ABC.L",
    is_existing: bool = False,
    weight: float = 0.0,
    policy: InvestablePolicy | ForcedZeroPolicy | None = None,
    rating: InvestmentRating = InvestmentRating.BUY,
) -> CuratorLaneIdentity:
    return CuratorLaneIdentity(
        ticker=ticker,
        company_name="Abc plc",
        is_existing_position=is_existing,
        current_weight_pct=weight,
        sector="Technology",
        industry="Semiconductors",
        policy=policy if policy is not None else InvestablePolicy(),
        rating=rating,
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


def test_data_quality_evidence_cannot_carry_valuation_fields() -> None:
    evidence = DataQualityRejectionLaneEvidence(
        identity=_identity(
            policy=ForcedZeroPolicy(reason=ForcedZeroReason.SELL),
            rating=InvestmentRating.SELL,
        ),
        rejection_reason="Gate failed.",
    )

    dumped = evidence.model_dump()
    assert "appraiser" not in dumped
    assert "researcher" not in dumped


def test_sentinel_rejection_evidence_cannot_carry_appraiser_fields() -> None:
    evidence = SentinelRejectionLaneEvidence(
        identity=_identity(
            policy=ForcedZeroPolicy(reason=ForcedZeroReason.STRONG_SELL),
            rating=InvestmentRating.STRONG_SELL,
        ),
        rejection_reason="Thesis broken.",
        live_thesis=_packed_thesis(),
        researcher=CompactResearcherEvidence(
            customer_segments="Customers", risks=("Risk",)
        ),
        strategist=CompactStrategistEvidence(
            thesis_summary="Summary",
            conviction="Low",
            thesis_risks=("Risk",),
            permanent_loss_scenarios=("Loss",),
        ),
        sentinel=CompactSentinelEvidence(
            customer_or_supplier_concentration="High",
            red_flag_verdict="Serious concern",
            reservations=False,
            material_data_gaps="None",
        ),
    )

    dumped = evidence.model_dump()
    assert "appraiser" not in dumped


def test_proposal_rejects_unordered_range() -> None:
    with pytest.raises(ValidationError, match="0 <= low <= target <= high"):
        CuratorProposal(
            allocation_date=date(2026, 8, 30),
            positions=(
                ProposedPosition(
                    ticker="ABC.L",
                    target_weight_pct=10.0,
                    acceptable_weight_low_pct=12.0,
                    acceptable_weight_high_pct=15.0,
                    rationale="Invalid range.",
                ),
            ),
            cash=ProposedCash(
                target_weight_pct=90.0,
                acceptable_weight_low_pct=85.0,
                acceptable_weight_high_pct=95.0,
                rationale="Cash.",
            ),
            shared_risk_clusters=(),
            portfolio_rationale="Test.",
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
