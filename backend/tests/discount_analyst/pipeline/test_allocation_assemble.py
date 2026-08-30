"""Tests for assembling and finalising Curator contracts."""

from datetime import date

import pytest

from discount_analyst.adapters.simulation.mock_outputs import (
    mock_curator_proposal,
    mock_appraiser_output,
    mock_deep_research,
    mock_rating_table_decision,
    mock_rating_table_gate_evaluation,
    mock_surveyor_candidate,
    mock_thesis,
)
from discount_analyst.agents.curator.schema import (
    CuratorProposal,
    ProposedCash,
    ProposedPosition,
    ProposedSharedRiskCluster,
)
from discount_analyst.agents.sentinel.schema import OverallRedFlagVerdict, ThesisVerdict
from discount_analyst.application.allocations.assemble import (
    CompletedLaneBundle,
    assemble_curator_input,
    completed_lane_bundle_from_verdict,
    source_run_ids_by_ticker,
)
from discount_analyst.application.allocations.errors import AllocationAssemblyError
from discount_analyst.application.allocations.finalise import (
    finalise_curator_proposal,
)
from discount_analyst.application.decisions.builders import (
    build_data_quality_rejection,
    build_sentinel_rejection,
    verdict_from_decision,
)
from discount_analyst.domain.allocations.actions import RebalanceAction
from discount_analyst.domain.allocations.invariants import AllocationInvariantError
from discount_analyst.domain.allocations.policy import ForcedZeroReason
from discount_analyst.domain.allocations.snapshot import (
    CurrentPortfolioSnapshot,
    CurrentPositionWeight,
)
from discount_analyst.domain.decisions.investment_rating import InvestmentRating
from discount_analyst.domain.decisions.margin_of_safety import MarginOfSafetyAssessment
from discount_analyst.domain.decisions.schema import (
    RatingTableDecision,
    RatingTableRationale,
)


ALLOCATION_DATE = date(2026, 8, 30)


def _cash_only() -> CurrentPortfolioSnapshot:
    return CurrentPortfolioSnapshot(
        as_of=ALLOCATION_DATE, positions=(), cash_weight_pct=100.0
    )


def _snapshot(
    *weights: tuple[str, float], cash_weight_pct: float
) -> CurrentPortfolioSnapshot:
    return CurrentPortfolioSnapshot(
        as_of=ALLOCATION_DATE,
        positions=tuple(
            CurrentPositionWeight(ticker=ticker, current_weight_pct=weight)
            for ticker, weight in weights
        ),
        cash_weight_pct=cash_weight_pct,
    )


def _rating_table_bundle(
    ticker: str,
    *,
    company_name: str | None = None,
    is_existing_position: bool,
    source_run_id: str,
    sector: str = "Technology",
    industry: str = "Semiconductors",
    rating: InvestmentRating | None = None,
) -> CompletedLaneBundle:
    candidate = mock_surveyor_candidate(ticker=ticker, company_name=company_name)
    thesis = mock_thesis(candidate)
    evaluation = mock_rating_table_gate_evaluation(candidate)
    appraiser_output = mock_appraiser_output(candidate)
    if rating is None:
        decision = mock_rating_table_decision(
            candidate,
            is_existing_position=is_existing_position,
            thesis=thesis,
            evaluation=evaluation,
        )
    else:
        mos = MarginOfSafetyAssessment.from_distribution(
            appraiser_output.valuation_distribution
        )
        decision = RatingTableDecision(
            decision_kind="rating_table",
            decision_rule_id="rating_table_v1",
            ticker=candidate.ticker,
            company_name=candidate.company_name,
            decision_date="2026-08-30",
            is_existing_position=is_existing_position,
            rating=rating,
            recommended_action="test",
            conviction=thesis.conviction_level,
            margin_of_safety=mos,
            rationale=RatingTableRationale(
                primary_driver="test",
                supporting_factors=[],
                mitigating_factors=[],
                red_flag_disposition="ok",
                data_gap_disposition="ok",
            ),
            thesis_expiry_note="unused",
        )
    return completed_lane_bundle_from_verdict(
        source_run_id=source_run_id,
        verdict=verdict_from_decision(decision),
        sector=sector,
        industry=industry,
        deep_research=mock_deep_research(candidate),
        thesis=thesis,
        evaluation=evaluation,
        appraiser_output=appraiser_output,
    )


def _sentinel_rejection_bundle(
    ticker: str, *, is_existing_position: bool, source_run_id: str
) -> CompletedLaneBundle:
    candidate = mock_surveyor_candidate(ticker=ticker)
    thesis = mock_thesis(candidate)
    evaluation = mock_rating_table_gate_evaluation(candidate).model_copy(
        update={
            "thesis_verdict": ThesisVerdict.BROKEN_DO_NOT_PROCEED,
            "red_flag_screen": mock_rating_table_gate_evaluation(
                candidate
            ).red_flag_screen.model_copy(
                update={
                    "overall_red_flag_verdict": OverallRedFlagVerdict.SERIOUS_CONCERN
                }
            ),
        }
    )
    decision = build_sentinel_rejection(
        evaluation,
        thesis,
        is_existing_position=is_existing_position,
        decision_date="2026-08-30",
    )
    return completed_lane_bundle_from_verdict(
        source_run_id=source_run_id,
        verdict=verdict_from_decision(decision),
        sector=candidate.sector,
        industry=candidate.industry,
        deep_research=mock_deep_research(candidate),
        thesis=thesis,
        evaluation=evaluation,
    )


def _data_quality_bundle(
    ticker: str, *, is_existing_position: bool, source_run_id: str
) -> CompletedLaneBundle:
    candidate = mock_surveyor_candidate(ticker=ticker)
    decision = build_data_quality_rejection(
        candidate.to_lane_context(),
        gate_failure_reason="Identity gate failed.",
        is_existing_position=is_existing_position,
        decision_date="2026-08-30",
    )
    return completed_lane_bundle_from_verdict(
        source_run_id=source_run_id,
        verdict=verdict_from_decision(decision),
        sector=candidate.sector,
        industry=candidate.industry,
    )


def _zero_row(ticker: str, *, rationale: str = "Forced zero.") -> ProposedPosition:
    return ProposedPosition(
        ticker=ticker,
        target_weight_pct=0.0,
        acceptable_weight_low_pct=0.0,
        acceptable_weight_high_pct=0.0,
        rationale=rationale,
    )


def test_assemble_cash_only_universe() -> None:
    packed = assemble_curator_input((), _cash_only(), ALLOCATION_DATE)

    assert packed.lanes == ()
    assert packed.snapshot.cash_weight_pct == 100.0


def test_assemble_maps_all_verdict_kinds() -> None:
    buy = _rating_table_bundle(
        "NVDA",
        is_existing_position=False,
        source_run_id="run-buy",
        rating=InvestmentRating.BUY,
    )
    existing_hold = _rating_table_bundle(
        "HELD",
        is_existing_position=True,
        source_run_id="run-hold",
        rating=InvestmentRating.HOLD,
    )
    new_hold = _rating_table_bundle(
        "WAIT",
        is_existing_position=False,
        source_run_id="run-new-hold",
        rating=InvestmentRating.HOLD,
    )
    rejected = _sentinel_rejection_bundle(
        "FAIL", is_existing_position=True, source_run_id="run-sent"
    )
    dqr = _data_quality_bundle(
        "JUNK", is_existing_position=False, source_run_id="run-dqr"
    )
    snapshot = _snapshot(("HELD", 10.0), ("FAIL", 5.0), cash_weight_pct=85.0)

    packed = assemble_curator_input(
        (buy, existing_hold, new_hold, rejected, dqr),
        snapshot,
        ALLOCATION_DATE,
    )

    kinds = {lane.identity.ticker: lane.decision_kind for lane in packed.lanes}
    assert kinds == {
        "NVDA": "rating_table",
        "HELD": "rating_table",
        "WAIT": "rating_table",
        "FAIL": "sentinel_rejection",
        "JUNK": "data_quality_rejection",
    }
    policies = {
        lane.identity.ticker: lane.identity.policy.kind for lane in packed.lanes
    }
    assert policies["NVDA"] == "investable"
    assert policies["HELD"] == "retain_or_reduce"
    assert policies["WAIT"] == "forced_zero"
    assert policies["FAIL"] == "forced_zero"
    assert policies["JUNK"] == "forced_zero"
    wait = next(lane for lane in packed.lanes if lane.identity.ticker == "WAIT")
    assert wait.identity.policy.kind == "forced_zero"
    assert wait.identity.policy.reason is ForcedZeroReason.NEW_HOLD
    junk = next(lane for lane in packed.lanes if lane.identity.ticker == "JUNK")
    assert not hasattr(junk, "appraiser")
    fail = next(lane for lane in packed.lanes if lane.identity.ticker == "FAIL")
    assert not hasattr(fail, "appraiser")
    buy_lane = next(lane for lane in packed.lanes if lane.identity.ticker == "NVDA")
    assert buy_lane.decision_kind == "rating_table"
    assert buy_lane.appraiser.expected_value > 0


def test_assemble_rejects_existing_position_missing_from_snapshot() -> None:
    bundle = _rating_table_bundle(
        "HELD",
        is_existing_position=True,
        source_run_id="run-hold",
        rating=InvestmentRating.HOLD,
    )

    with pytest.raises(AllocationAssemblyError, match="missing from the current"):
        assemble_curator_input((bundle,), _cash_only(), ALLOCATION_DATE)


def test_assemble_rejects_snapshot_position_without_lane() -> None:
    snapshot = _snapshot(("ORPHAN", 20.0), cash_weight_pct=80.0)

    with pytest.raises(AllocationAssemblyError, match="has no completed lane"):
        assemble_curator_input((), snapshot, ALLOCATION_DATE)


def test_assemble_rejects_valuation_on_data_quality_lane() -> None:
    bundle = _data_quality_bundle(
        "JUNK", is_existing_position=False, source_run_id="run-dqr"
    )
    valued = _rating_table_bundle(
        "JUNK",
        is_existing_position=False,
        source_run_id="run-dqr",
        rating=InvestmentRating.SELL,
    )
    mixed = CompletedLaneBundle(
        source_run_id=bundle.source_run_id,
        ticker=bundle.ticker,
        company_name=bundle.company_name,
        is_existing_position=bundle.is_existing_position,
        rating=bundle.rating,
        decision_kind=bundle.decision_kind,
        rejection_reason=bundle.rejection_reason,
        sector=bundle.sector,
        industry=bundle.industry,
        appraiser_output=valued.appraiser_output,
    )

    with pytest.raises(AllocationAssemblyError, match="cannot carry"):
        assemble_curator_input((mixed,), _cash_only(), ALLOCATION_DATE)


def test_finalise_cash_only_allocation() -> None:
    packed = assemble_curator_input((), _cash_only(), ALLOCATION_DATE)
    proposal = CuratorProposal(
        allocation_date=ALLOCATION_DATE,
        positions=(),
        cash=ProposedCash(
            target_weight_pct=100.0,
            acceptable_weight_low_pct=100.0,
            acceptable_weight_high_pct=100.0,
            rationale="No names.",
        ),
        shared_risk_clusters=(),
        portfolio_rationale="Cash only.",
    )

    allocation = finalise_curator_proposal(proposal, packed, {})

    assert allocation.cash.target_weight_pct == 100.0
    assert allocation.positions == ()


def test_finalise_preserves_proposal_numbers_and_derives_actions() -> None:
    buy = _rating_table_bundle(
        "NVDA",
        company_name="NVIDIA",
        is_existing_position=False,
        source_run_id="run-nvda",
        rating=InvestmentRating.BUY,
    )
    held = _rating_table_bundle(
        "HELD",
        company_name="Held Co",
        is_existing_position=True,
        source_run_id="run-held",
        rating=InvestmentRating.HOLD,
    )
    rejected = _sentinel_rejection_bundle(
        "FAIL", is_existing_position=True, source_run_id="run-fail"
    )
    snapshot = _snapshot(("HELD", 10.0), ("FAIL", 8.0), cash_weight_pct=82.0)
    bundles = (buy, held, rejected)
    packed = assemble_curator_input(bundles, snapshot, ALLOCATION_DATE)
    proposal = CuratorProposal(
        allocation_date=ALLOCATION_DATE,
        positions=(
            ProposedPosition(
                ticker="NVDA",
                target_weight_pct=12.0,
                acceptable_weight_low_pct=10.0,
                acceptable_weight_high_pct=14.0,
                rationale="Best independent idea.",
            ),
            ProposedPosition(
                ticker="HELD",
                target_weight_pct=8.0,
                acceptable_weight_low_pct=6.0,
                acceptable_weight_high_pct=10.0,
                rationale="Retain within band.",
            ),
            _zero_row("FAIL", rationale="Forced exit."),
        ),
        cash=ProposedCash(
            target_weight_pct=80.0,
            acceptable_weight_low_pct=76.0,
            acceptable_weight_high_pct=84.0,
            rationale="Residual cash.",
        ),
        shared_risk_clusters=(),
        portfolio_rationale="Concentrate in NVDA.",
    )
    before = proposal.model_dump()

    allocation = finalise_curator_proposal(
        proposal, packed, source_run_ids_by_ticker(bundles)
    )

    assert proposal.model_dump() == before
    by_ticker = {row.ticker: row for row in allocation.positions}
    assert by_ticker["NVDA"].target_weight_pct == 12.0
    assert by_ticker["NVDA"].action is RebalanceAction.ENTER
    assert by_ticker["NVDA"].source_run_id == "run-nvda"
    assert by_ticker["HELD"].action is RebalanceAction.HOLD
    assert by_ticker["FAIL"].action is RebalanceAction.EXIT
    assert by_ticker["FAIL"].target_weight_pct == 0.0


def test_finalise_rejects_existing_hold_increase() -> None:
    held = _rating_table_bundle(
        "HELD",
        is_existing_position=True,
        source_run_id="run-held",
        rating=InvestmentRating.HOLD,
    )
    snapshot = _snapshot(("HELD", 10.0), cash_weight_pct=90.0)
    packed = assemble_curator_input((held,), snapshot, ALLOCATION_DATE)
    proposal = CuratorProposal(
        allocation_date=ALLOCATION_DATE,
        positions=(
            ProposedPosition(
                ticker="HELD",
                target_weight_pct=12.0,
                acceptable_weight_low_pct=10.0,
                acceptable_weight_high_pct=12.0,
                rationale="Illegal increase.",
            ),
        ),
        cash=ProposedCash(
            target_weight_pct=88.0,
            acceptable_weight_low_pct=80.0,
            acceptable_weight_high_pct=90.0,
            rationale="Cash.",
        ),
        shared_risk_clusters=(),
        portfolio_rationale="Bad HOLD increase.",
    )

    with pytest.raises(AllocationInvariantError, match="Retain-or-reduce"):
        finalise_curator_proposal(proposal, packed, source_run_ids_by_ticker((held,)))


def test_finalise_rejects_nonzero_forced_zero() -> None:
    rejected = _data_quality_bundle(
        "JUNK", is_existing_position=False, source_run_id="run-dqr"
    )
    packed = assemble_curator_input((rejected,), _cash_only(), ALLOCATION_DATE)
    proposal = CuratorProposal(
        allocation_date=ALLOCATION_DATE,
        positions=(
            ProposedPosition(
                ticker="JUNK",
                target_weight_pct=5.0,
                acceptable_weight_low_pct=0.0,
                acceptable_weight_high_pct=5.0,
                rationale="Illegal residual.",
            ),
        ),
        cash=ProposedCash(
            target_weight_pct=95.0,
            acceptable_weight_low_pct=90.0,
            acceptable_weight_high_pct=100.0,
            rationale="Cash.",
        ),
        shared_risk_clusters=(),
        portfolio_rationale="Bad forced zero.",
    )

    with pytest.raises(AllocationInvariantError, match="Forced-zero"):
        finalise_curator_proposal(
            proposal, packed, source_run_ids_by_ticker((rejected,))
        )


def test_finalise_enforces_company_cap_across_duplicate_names() -> None:
    arm_us = _rating_table_bundle(
        "ARM",
        company_name="Arm Holdings",
        is_existing_position=False,
        source_run_id="run-arm-us",
        rating=InvestmentRating.BUY,
    )
    arm_uk = _rating_table_bundle(
        "ARM.L",
        company_name="ARM HOLDINGS",
        is_existing_position=False,
        source_run_id="run-arm-uk",
        rating=InvestmentRating.BUY,
    )
    packed = assemble_curator_input((arm_us, arm_uk), _cash_only(), ALLOCATION_DATE)
    proposal = CuratorProposal(
        allocation_date=ALLOCATION_DATE,
        positions=(
            ProposedPosition(
                ticker="ARM",
                target_weight_pct=10.0,
                acceptable_weight_low_pct=8.0,
                acceptable_weight_high_pct=12.0,
                rationale="US line.",
            ),
            ProposedPosition(
                ticker="ARM.L",
                target_weight_pct=10.0,
                acceptable_weight_low_pct=8.0,
                acceptable_weight_high_pct=12.0,
                rationale="UK line.",
            ),
        ),
        cash=ProposedCash(
            target_weight_pct=80.0,
            acceptable_weight_low_pct=70.0,
            acceptable_weight_high_pct=90.0,
            rationale="Cash.",
        ),
        shared_risk_clusters=(),
        portfolio_rationale="Dual listing exceeds cap.",
    )

    with pytest.raises(AllocationInvariantError, match="15.0% cap"):
        finalise_curator_proposal(
            proposal, packed, source_run_ids_by_ticker((arm_us, arm_uk))
        )


def test_semiconductor_cluster_reduces_weaker_name() -> None:
    tsmc = _rating_table_bundle(
        "TSM",
        company_name="TSMC",
        is_existing_position=False,
        source_run_id="run-tsm",
        sector="Technology",
        industry="Semiconductors",
        rating=InvestmentRating.STRONG_BUY,
    )
    amat = _rating_table_bundle(
        "AMAT",
        company_name="Applied Materials",
        is_existing_position=False,
        source_run_id="run-amat",
        sector="Technology",
        industry="Semiconductor Equipment",
        rating=InvestmentRating.BUY,
    )
    bundles = (tsmc, amat)
    packed = assemble_curator_input(bundles, _cash_only(), ALLOCATION_DATE)
    proposal = CuratorProposal(
        allocation_date=ALLOCATION_DATE,
        positions=(
            ProposedPosition(
                ticker="TSM",
                target_weight_pct=12.0,
                acceptable_weight_low_pct=10.0,
                acceptable_weight_high_pct=14.0,
                rationale="Stronger independent foundry idea.",
            ),
            ProposedPosition(
                ticker="AMAT",
                target_weight_pct=4.0,
                acceptable_weight_low_pct=2.0,
                acceptable_weight_high_pct=6.0,
                rationale="Reduced because it shares TSMC's supply-chain failure.",
            ),
        ),
        cash=ProposedCash(
            target_weight_pct=84.0,
            acceptable_weight_low_pct=80.0,
            acceptable_weight_high_pct=88.0,
            rationale="Unused capital stays in cash.",
        ),
        shared_risk_clusters=(
            ProposedSharedRiskCluster(
                label="Semiconductor supply chain",
                member_tickers=("TSM", "AMAT"),
                mechanism=(
                    "Both names fail if leading-edge foundry capex and AI "
                    "accelerator demand collapse together."
                ),
                allocation_effect=(
                    "Reduced AMAT, the weaker correlated exposure, rather than "
                    "adding a third semiconductor name."
                ),
            ),
        ),
        portfolio_rationale="Keep the stronger foundry idea; penalise the tool name.",
    )

    allocation = finalise_curator_proposal(
        proposal, packed, source_run_ids_by_ticker(bundles)
    )

    by_ticker = {row.ticker: row for row in allocation.positions}
    assert by_ticker["AMAT"].target_weight_pct < by_ticker["TSM"].target_weight_pct
    assert len(allocation.shared_risk_clusters) == 1
    cluster = allocation.shared_risk_clusters[0]
    assert cluster.label == "Semiconductor supply chain"
    assert set(cluster.member_tickers) == {"TSM", "AMAT"}
    assert "weaker" in cluster.allocation_effect.lower()


def test_mock_proposal_caps_dual_listing_company_highs() -> None:
    us = _rating_table_bundle(
        "ARM",
        company_name="Arm Holdings",
        is_existing_position=False,
        source_run_id="run-arm-us",
        rating=InvestmentRating.BUY,
    )
    uk = _rating_table_bundle(
        "ARM.L",
        company_name="Arm Holdings",
        is_existing_position=False,
        source_run_id="run-arm-uk",
        rating=InvestmentRating.BUY,
    )
    bundles = (us, uk)
    packed = assemble_curator_input(bundles, _cash_only(), ALLOCATION_DATE)
    proposal = mock_curator_proposal(packed)
    allocation = finalise_curator_proposal(
        proposal, packed, source_run_ids_by_ticker(bundles)
    )

    highs = sum(row.acceptable_weight_high_pct for row in allocation.positions)
    assert highs <= 15.0
    targets = sum(row.target_weight_pct for row in allocation.positions)
    assert targets <= 15.0
