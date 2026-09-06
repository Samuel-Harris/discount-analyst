"""Tests for assembling and finalising Curator contracts."""

from datetime import date

import pytest

from discount_analyst.adapters.simulation.mock_outputs import (
    mock_curator_proposal,
    mock_appraiser_output,
    mock_deep_research,
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
from discount_analyst.application.allocations.assemble import (
    DqrLaneBundle,
    ValuedLaneBundle,
    assemble_curator_job,
    dqr_lane_bundle,
    source_run_ids_by_ticker,
    valued_lane_bundle,
)
from discount_analyst.application.allocations.errors import AllocationAssemblyError
from discount_analyst.application.allocations.finalise import (
    finalise_curator_proposal,
    synthesise_cash_only_allocation,
)
from discount_analyst.application.decisions.builders import (
    build_appraised_decision,
    build_data_quality_rejection,
)
from discount_analyst.domain.allocations.actions import RebalanceAction
from discount_analyst.domain.allocations.invariants import AllocationInvariantError
from discount_analyst.domain.allocations.snapshot import (
    CurrentPortfolioSnapshot,
    CurrentPositionWeight,
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


def _appraised_bundle(
    ticker: str,
    *,
    company_name: str | None = None,
    is_existing_position: bool,
    source_run_id: str,
    sector: str = "Technology",
    industry: str = "Semiconductors",
) -> ValuedLaneBundle:
    candidate = mock_surveyor_candidate(ticker=ticker, company_name=company_name)
    thesis = mock_thesis(candidate)
    evaluation = mock_rating_table_gate_evaluation(candidate)
    appraiser_output = mock_appraiser_output(candidate)
    decision = build_appraised_decision(
        candidate.to_lane_context(),
        is_existing_position=is_existing_position,
        decision_date="2026-08-30",
    )
    return valued_lane_bundle(
        source_run_id=source_run_id,
        decision=decision,
        sector=sector,
        industry=industry,
        deep_research=mock_deep_research(candidate),
        thesis=thesis,
        evaluation=evaluation,
        appraiser_output=appraiser_output,
    )


def _data_quality_bundle(
    ticker: str, *, is_existing_position: bool, source_run_id: str
) -> DqrLaneBundle:
    candidate = mock_surveyor_candidate(ticker=ticker)
    decision = build_data_quality_rejection(
        candidate.to_lane_context(),
        gate_failure_reason="Identity gate failed.",
        is_existing_position=is_existing_position,
        decision_date="2026-08-30",
    )
    return dqr_lane_bundle(
        source_run_id=source_run_id,
        decision=decision,
        sector=candidate.sector,
        industry=candidate.industry,
    )


def test_assemble_cash_only_universe() -> None:
    job = assemble_curator_job((), _cash_only(), ALLOCATION_DATE)

    assert job.curator_input.lanes == ()
    assert job.dqr_stamps == ()
    assert job.curator_input.snapshot.cash_weight_pct == 100.0


def test_assemble_omits_dqr_from_llm_pack() -> None:
    buy = _appraised_bundle(
        "NVDA",
        is_existing_position=False,
        source_run_id="run-buy",
    )
    held = _appraised_bundle(
        "HELD",
        is_existing_position=True,
        source_run_id="run-hold",
    )
    dqr = _data_quality_bundle(
        "JUNK", is_existing_position=False, source_run_id="run-dqr"
    )
    snapshot = _snapshot(("HELD", 10.0), ("JUNK", 8.0), cash_weight_pct=82.0)

    job = assemble_curator_job((buy, held), snapshot, ALLOCATION_DATE, dqr=(dqr,))

    packed_tickers = {lane.identity.ticker for lane in job.curator_input.lanes}
    assert packed_tickers == {"NVDA", "HELD"}
    assert {stamp.ticker for stamp in job.dqr_stamps} == {"JUNK"}
    llm_tickers = {
        position.ticker for position in job.curator_input.snapshot.positions
    }
    assert llm_tickers == {"HELD"}
    assert job.curator_input.snapshot.cash_weight_pct == 90.0
    assert job.ledger_cash_weight_pct == 82.0
    nvda = next(
        lane for lane in job.curator_input.lanes if lane.identity.ticker == "NVDA"
    )
    assert nvda.appraiser.expected_value > 0
    assert not hasattr(nvda.identity, "policy")
    assert not hasattr(nvda.identity, "rating")


def test_assemble_rejects_existing_position_missing_from_snapshot() -> None:
    bundle = _appraised_bundle(
        "HELD",
        is_existing_position=True,
        source_run_id="run-hold",
    )

    with pytest.raises(AllocationAssemblyError, match="missing from the current"):
        assemble_curator_job((bundle,), _cash_only(), ALLOCATION_DATE)


def test_assemble_rejects_snapshot_position_without_lane() -> None:
    snapshot = _snapshot(("ORPHAN", 20.0), cash_weight_pct=80.0)

    with pytest.raises(AllocationAssemblyError, match="has no completed lane"):
        assemble_curator_job((), snapshot, ALLOCATION_DATE)


def test_finalise_cash_only_allocation() -> None:
    job = assemble_curator_job((), _cash_only(), ALLOCATION_DATE)
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

    allocation = finalise_curator_proposal(proposal, job)

    assert allocation.cash.target_weight_pct == 100.0
    assert allocation.positions == ()


def test_finalise_stamps_dqr_zeros_and_allows_holding_increase() -> None:
    buy = _appraised_bundle(
        "NVDA",
        company_name="NVIDIA",
        is_existing_position=False,
        source_run_id="run-nvda",
    )
    held = _appraised_bundle(
        "HELD",
        company_name="Held Co",
        is_existing_position=True,
        source_run_id="run-held",
    )
    dqr = _data_quality_bundle(
        "JUNK", is_existing_position=True, source_run_id="run-dqr"
    )
    snapshot = _snapshot(("HELD", 10.0), ("JUNK", 8.0), cash_weight_pct=82.0)
    bundles = (buy, held)
    job = assemble_curator_job(bundles, snapshot, ALLOCATION_DATE, dqr=(dqr,))
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
                target_weight_pct=12.0,
                acceptable_weight_low_pct=11.0,
                acceptable_weight_high_pct=13.0,
                rationale="Increase an existing holding.",
            ),
        ),
        cash=ProposedCash(
            target_weight_pct=76.0,
            acceptable_weight_low_pct=72.0,
            acceptable_weight_high_pct=80.0,
            rationale="Residual cash.",
        ),
        shared_risk_clusters=(),
        portfolio_rationale="Concentrate in NVDA and add to HELD.",
    )
    before = proposal.model_dump()

    allocation = finalise_curator_proposal(proposal, job)

    assert proposal.model_dump() == before
    by_ticker = {row.ticker: row for row in allocation.positions}
    assert by_ticker["NVDA"].target_weight_pct == 12.0
    assert by_ticker["NVDA"].action is RebalanceAction.ENTER
    assert by_ticker["NVDA"].source_run_id == "run-nvda"
    assert by_ticker["HELD"].action is RebalanceAction.INCREASE
    assert by_ticker["HELD"].target_weight_pct == 12.0
    assert by_ticker["JUNK"].action is RebalanceAction.EXIT
    assert by_ticker["JUNK"].target_weight_pct == 0.0
    assert by_ticker["JUNK"].rationale.startswith("Data-quality gate failed:")
    assert allocation.cash.current_weight_pct == 82.0
    assert "policy" not in by_ticker["NVDA"].model_dump()


def test_synthesise_all_dqr_skips_llm_pack() -> None:
    dqr = _data_quality_bundle(
        "JUNK", is_existing_position=True, source_run_id="run-dqr"
    )
    snapshot = _snapshot(("JUNK", 8.0), cash_weight_pct=92.0)
    job = assemble_curator_job((), snapshot, ALLOCATION_DATE, dqr=(dqr,))

    assert job.curator_input.lanes == ()
    assert job.curator_input.snapshot.positions == ()
    assert job.curator_input.snapshot.cash_weight_pct == 100.0
    assert job.ledger_cash_weight_pct == 92.0
    allocation = synthesise_cash_only_allocation(job)

    assert allocation.cash.target_weight_pct == 100.0
    assert allocation.cash.current_weight_pct == 92.0
    assert allocation.positions[0].ticker == "JUNK"
    assert allocation.positions[0].target_weight_pct == 0.0
    assert allocation.positions[0].action is RebalanceAction.EXIT


def test_finalise_enforces_company_cap_across_duplicate_names() -> None:
    arm_us = _appraised_bundle(
        "ARM",
        company_name="Arm Holdings",
        is_existing_position=False,
        source_run_id="run-arm-us",
    )
    arm_uk = _appraised_bundle(
        "ARM.L",
        company_name="ARM HOLDINGS",
        is_existing_position=False,
        source_run_id="run-arm-uk",
    )
    job = assemble_curator_job((arm_us, arm_uk), _cash_only(), ALLOCATION_DATE)
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
        finalise_curator_proposal(proposal, job)


def test_semiconductor_cluster_reduces_weaker_name() -> None:
    tsmc = _appraised_bundle(
        "TSM",
        company_name="TSMC",
        is_existing_position=False,
        source_run_id="run-tsm",
        sector="Technology",
        industry="Semiconductors",
    )
    amat = _appraised_bundle(
        "AMAT",
        company_name="Applied Materials",
        is_existing_position=False,
        source_run_id="run-amat",
        sector="Technology",
        industry="Semiconductor Equipment",
    )
    bundles = (tsmc, amat)
    job = assemble_curator_job(bundles, _cash_only(), ALLOCATION_DATE)
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

    allocation = finalise_curator_proposal(proposal, job)

    by_ticker = {row.ticker: row for row in allocation.positions}
    assert by_ticker["AMAT"].target_weight_pct < by_ticker["TSM"].target_weight_pct
    assert len(allocation.shared_risk_clusters) == 1
    cluster = allocation.shared_risk_clusters[0]
    assert cluster.label == "Semiconductor supply chain"
    assert set(cluster.member_tickers) == {"TSM", "AMAT"}
    assert "weaker" in cluster.allocation_effect.lower()


def test_mock_proposal_caps_dual_listing_company_highs() -> None:
    us = _appraised_bundle(
        "ARM",
        company_name="Arm Holdings",
        is_existing_position=False,
        source_run_id="run-arm-us",
    )
    uk = _appraised_bundle(
        "ARM.L",
        company_name="Arm Holdings",
        is_existing_position=False,
        source_run_id="run-arm-uk",
    )
    bundles = (us, uk)
    job = assemble_curator_job(bundles, _cash_only(), ALLOCATION_DATE)
    proposal = mock_curator_proposal(job.curator_input)
    allocation = finalise_curator_proposal(proposal, job)

    highs = sum(row.acceptable_weight_high_pct for row in allocation.positions)
    assert highs <= 15.0
    targets = sum(row.target_weight_pct for row in allocation.positions)
    assert targets <= 15.0
    assert source_run_ids_by_ticker(bundles)["arm"] == "run-arm-us"
