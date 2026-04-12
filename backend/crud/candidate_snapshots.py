"""Map between Surveyor candidate payloads and persisted CandidateSnapshot rows."""

from __future__ import annotations

from backend.crud.db_utils import new_id
from backend.db.models import CandidateSnapshot
from discount_analyst.agents.surveyor.schema import KeyMetrics, SurveyorCandidate


def candidate_to_snapshot(
    *,
    candidate: SurveyorCandidate,
    sort_order: int,
    workflow_agent_execution_id: str | None,
    agent_execution_id: str | None,
) -> CandidateSnapshot:
    return CandidateSnapshot(
        id=new_id(),
        workflow_agent_execution_id=workflow_agent_execution_id,
        agent_execution_id=agent_execution_id,
        sort_order=sort_order,
        ticker=candidate.ticker,
        company_name=candidate.company_name,
        exchange=candidate.exchange.value,
        currency=candidate.currency.value,
        market_cap_local=candidate.market_cap_local,
        market_cap_display=candidate.market_cap_display,
        sector=candidate.sector,
        industry=candidate.industry,
        analyst_coverage_count=candidate.analyst_coverage_count,
        trailing_pe=candidate.key_metrics.trailing_pe,
        ev_ebit=candidate.key_metrics.ev_ebit,
        price_to_book=candidate.key_metrics.price_to_book,
        revenue_growth_3y_cagr_pct=candidate.key_metrics.revenue_growth_3y_cagr_pct,
        free_cash_flow_yield_pct=candidate.key_metrics.free_cash_flow_yield_pct,
        net_debt_to_ebitda=candidate.key_metrics.net_debt_to_ebitda,
        piotroski_f_score=candidate.key_metrics.piotroski_f_score,
        altman_z_score=candidate.key_metrics.altman_z_score,
        insider_buying_last_6m=candidate.key_metrics.insider_buying_last_6m,
        rationale=candidate.rationale,
        red_flags=candidate.red_flags,
        data_gaps=candidate.data_gaps,
    )


def snapshot_to_candidate(snapshot: CandidateSnapshot) -> SurveyorCandidate:
    return SurveyorCandidate(
        ticker=snapshot.ticker,
        company_name=snapshot.company_name,
        exchange=snapshot.exchange,
        currency=snapshot.currency,
        market_cap_local=snapshot.market_cap_local,
        market_cap_display=snapshot.market_cap_display,
        sector=snapshot.sector,
        industry=snapshot.industry,
        analyst_coverage_count=snapshot.analyst_coverage_count,
        key_metrics=KeyMetrics(
            trailing_pe=snapshot.trailing_pe,
            ev_ebit=snapshot.ev_ebit,
            price_to_book=snapshot.price_to_book,
            revenue_growth_3y_cagr_pct=snapshot.revenue_growth_3y_cagr_pct,
            free_cash_flow_yield_pct=snapshot.free_cash_flow_yield_pct,
            net_debt_to_ebitda=snapshot.net_debt_to_ebitda,
            piotroski_f_score=snapshot.piotroski_f_score,
            altman_z_score=snapshot.altman_z_score,
            insider_buying_last_6m=snapshot.insider_buying_last_6m,
        ),
        rationale=snapshot.rationale,
        red_flags=snapshot.red_flags,
        data_gaps=snapshot.data_gaps,
    )
