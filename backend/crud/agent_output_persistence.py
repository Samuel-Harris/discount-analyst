"""Persist structured agent outputs (research, thesis, evaluation, appraiser, verdicts, DCF)."""

from __future__ import annotations

import json
from datetime import date
from typing import Any, cast

from sqlalchemy import delete, select
from sqlmodel import Session, col

from backend.crud.candidate_snapshots import candidate_to_snapshot
from backend.crud.db_utils import new_id
from backend.db.models import (
    AgentExecution,
    AppraiserReport,
    CandidateSnapshot,
    DcfValuation,
    DecisionTypeDb,
    EvaluationCaveat,
    EvaluationQuestionAssessment,
    EvaluationReport,
    MispricingThesis,
    MispricingThesisEvaluationQuestion,
    MispricingThesisFalsificationCondition,
    MispricingThesisPermanentLossScenario,
    MispricingThesisRisk,
    ResearchReport,
    ResearchReportClosedGap,
    ResearchReportMaterialOpenGap,
    ResearchReportNarrativeMonitoringSignal,
    ResearchReportPotentialCatalyst,
    ResearchReportRemainingOpenGap,
    ResearchReportRisk,
    ResearchReportSourceNote,
    Run,
    RunFinalDecision,
    RunFinalDecisionMitigatingFactor,
    RunFinalDecisionSupportingFactor,
    WorkflowAgentExecution,
)
from discount_analyst.agents.appraiser.schema import AppraiserOutput
from discount_analyst.agents.profiler.schema import ProfilerOutput
from discount_analyst.agents.researcher.schema import (
    DeepResearchReport,
)
from discount_analyst.agents.sentinel.schema import (
    EvaluationReport as EvaluationReportSchema,
)
from discount_analyst.agents.strategist.schema import (
    MispricingThesis as MispricingThesisSchema,
)
from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.valuation.data_types import DCFAnalysisResult


def persist_surveyor_output(
    session: Session,
    execution: WorkflowAgentExecution,
    output_json: str,
) -> None:
    raw: object = json.loads(output_json)
    candidates_raw: list[object] = []
    if isinstance(raw, dict):
        raw_map = cast(dict[str, Any], raw)
        got = raw_map.get("candidates", [])
        if isinstance(got, list):
            candidates_raw = cast(list[Any], got)
    candidates = [SurveyorCandidate.model_validate(c) for c in candidates_raw]
    session.exec(
        delete(CandidateSnapshot).where(
            col(CandidateSnapshot.workflow_agent_execution_id) == execution.id
        )
    )
    for idx, candidate in enumerate(candidates):
        session.add(
            candidate_to_snapshot(
                candidate=candidate,
                sort_order=idx,
                workflow_agent_execution_id=execution.id,
                agent_execution_id=None,
            )
        )


def persist_profiler_output(
    session: Session,
    execution: AgentExecution,
    output_json: str,
) -> None:
    output = ProfilerOutput.model_validate_json(output_json)
    session.exec(
        delete(CandidateSnapshot).where(
            col(CandidateSnapshot.agent_execution_id) == execution.id
        )
    )
    snap = candidate_to_snapshot(
        candidate=output.candidate,
        sort_order=0,
        workflow_agent_execution_id=None,
        agent_execution_id=execution.id,
    )
    session.add(snap)
    run = session.get(Run, execution.run_id)
    if run is not None:
        run.candidate_snapshot_id = snap.id
        run.company_name = output.candidate.company_name


def replace_research_report(
    session: Session,
    execution: AgentExecution,
    output_json: str,
) -> None:
    output = DeepResearchReport.model_validate_json(output_json)
    run = session.get(Run, execution.run_id)
    if run is None or run.candidate_snapshot_id is None:
        return
    existing = session.scalars(
        select(ResearchReport).where(
            col(ResearchReport.agent_execution_id) == execution.id
        )
    ).first()
    if existing is not None:
        session.exec(
            delete(ResearchReportNarrativeMonitoringSignal).where(
                col(ResearchReportNarrativeMonitoringSignal.research_report_id)
                == existing.id
            )
        )
        session.exec(
            delete(ResearchReportRisk).where(
                col(ResearchReportRisk.research_report_id) == existing.id
            )
        )
        session.exec(
            delete(ResearchReportPotentialCatalyst).where(
                col(ResearchReportPotentialCatalyst.research_report_id) == existing.id
            )
        )
        session.exec(
            delete(ResearchReportClosedGap).where(
                col(ResearchReportClosedGap.research_report_id) == existing.id
            )
        )
        session.exec(
            delete(ResearchReportRemainingOpenGap).where(
                col(ResearchReportRemainingOpenGap.research_report_id) == existing.id
            )
        )
        session.exec(
            delete(ResearchReportMaterialOpenGap).where(
                col(ResearchReportMaterialOpenGap.research_report_id) == existing.id
            )
        )
        session.exec(
            delete(ResearchReportSourceNote).where(
                col(ResearchReportSourceNote.research_report_id) == existing.id
            )
        )
        session.delete(existing)
        session.flush()

    report = ResearchReport(
        id=new_id(),
        agent_execution_id=execution.id,
        candidate_snapshot_id=run.candidate_snapshot_id,
        executive_overview=output.executive_overview,
        products_and_services=output.business_model.products_and_services,
        customer_segments=output.business_model.customer_segments,
        unit_economics=output.business_model.unit_economics,
        competitive_positioning=output.business_model.competitive_positioning,
        moat_and_durability=output.business_model.moat_and_durability,
        updated_trailing_pe=output.financial_profile.key_metrics_updated.trailing_pe,
        updated_ev_ebit=output.financial_profile.key_metrics_updated.ev_ebit,
        updated_price_to_book=output.financial_profile.key_metrics_updated.price_to_book,
        updated_revenue_growth_3y_cagr_pct=output.financial_profile.key_metrics_updated.revenue_growth_3y_cagr_pct,
        updated_free_cash_flow_yield_pct=output.financial_profile.key_metrics_updated.free_cash_flow_yield_pct,
        updated_net_debt_to_ebitda=output.financial_profile.key_metrics_updated.net_debt_to_ebitda,
        updated_piotroski_f_score=output.financial_profile.key_metrics_updated.piotroski_f_score,
        updated_altman_z_score=output.financial_profile.key_metrics_updated.altman_z_score,
        updated_insider_buying_last_6m=output.financial_profile.key_metrics_updated.insider_buying_last_6m,
        revenue_and_growth_quality=output.financial_profile.revenue_and_growth_quality,
        profitability_and_margin_structure=output.financial_profile.profitability_and_margin_structure,
        balance_sheet_and_liquidity=output.financial_profile.balance_sheet_and_liquidity,
        cash_flow_and_capital_intensity=output.financial_profile.cash_flow_and_capital_intensity,
        capital_allocation=output.financial_profile.capital_allocation,
        leadership_and_execution=output.management_assessment.leadership_and_execution,
        governance_and_alignment=output.management_assessment.governance_and_alignment,
        communication_quality=output.management_assessment.communication_quality,
        key_concerns=output.management_assessment.key_concerns,
        dominant_narrative=output.market_narrative.dominant_narrative,
        bull_case_in_market=output.market_narrative.bull_case_in_market,
        bear_case_in_market=output.market_narrative.bear_case_in_market,
        expectations_implied_by_price=output.market_narrative.expectations_implied_by_price,
        where_expectations_may_be_wrong=output.market_narrative.where_expectations_may_be_wrong,
        original_data_gaps=output.data_gaps_update.original_data_gaps,
    )
    session.add(report)
    for idx, value in enumerate(output.market_narrative.narrative_monitoring_signals):
        session.add(
            ResearchReportNarrativeMonitoringSignal(
                id=new_id(),
                research_report_id=report.id,
                sort_order=idx,
                signal=value,
            )
        )
    for idx, value in enumerate(output.risks):
        session.add(
            ResearchReportRisk(
                id=new_id(),
                research_report_id=report.id,
                sort_order=idx,
                risk=value,
            )
        )
    for idx, value in enumerate(output.potential_catalysts):
        session.add(
            ResearchReportPotentialCatalyst(
                id=new_id(),
                research_report_id=report.id,
                sort_order=idx,
                catalyst=value,
            )
        )
    for idx, value in enumerate(output.data_gaps_update.closed_gaps):
        session.add(
            ResearchReportClosedGap(
                id=new_id(),
                research_report_id=report.id,
                sort_order=idx,
                gap_text=value,
            )
        )
    for idx, value in enumerate(output.data_gaps_update.remaining_open_gaps):
        session.add(
            ResearchReportRemainingOpenGap(
                id=new_id(),
                research_report_id=report.id,
                sort_order=idx,
                gap_text=value,
            )
        )
    for idx, value in enumerate(output.data_gaps_update.material_open_gaps):
        session.add(
            ResearchReportMaterialOpenGap(
                id=new_id(),
                research_report_id=report.id,
                sort_order=idx,
                gap_text=value,
            )
        )
    for idx, value in enumerate(output.source_notes):
        session.add(
            ResearchReportSourceNote(
                id=new_id(),
                research_report_id=report.id,
                sort_order=idx,
                source_note=value,
            )
        )


def replace_mispricing_thesis(
    session: Session,
    execution: AgentExecution,
    output_json: str,
) -> None:
    output = MispricingThesisSchema.model_validate_json(output_json)
    existing = session.scalars(
        select(MispricingThesis).where(
            col(MispricingThesis.agent_execution_id) == execution.id
        )
    ).first()
    if existing is not None:
        session.exec(
            delete(MispricingThesisFalsificationCondition).where(
                col(MispricingThesisFalsificationCondition.mispricing_thesis_id)
                == existing.id
            )
        )
        session.exec(
            delete(MispricingThesisRisk).where(
                col(MispricingThesisRisk.mispricing_thesis_id) == existing.id
            )
        )
        session.exec(
            delete(MispricingThesisEvaluationQuestion).where(
                col(MispricingThesisEvaluationQuestion.mispricing_thesis_id)
                == existing.id
            )
        )
        session.exec(
            delete(MispricingThesisPermanentLossScenario).where(
                col(MispricingThesisPermanentLossScenario.mispricing_thesis_id)
                == existing.id
            )
        )
        session.delete(existing)
        session.flush()
    row = MispricingThesis(
        id=new_id(),
        agent_execution_id=execution.id,
        mispricing_type=output.mispricing_type,
        market_belief=output.market_belief,
        mispricing_argument=output.mispricing_argument,
        resolution_mechanism=output.resolution_mechanism,
        conviction_level=output.conviction_level,
    )
    session.add(row)
    for idx, value in enumerate(output.falsification_conditions):
        session.add(
            MispricingThesisFalsificationCondition(
                id=new_id(),
                mispricing_thesis_id=row.id,
                sort_order=idx,
                condition_text=value,
            )
        )
    for idx, value in enumerate(output.thesis_risks):
        session.add(
            MispricingThesisRisk(
                id=new_id(),
                mispricing_thesis_id=row.id,
                sort_order=idx,
                risk_text=value,
            )
        )
    for idx, value in enumerate(output.evaluation_questions):
        session.add(
            MispricingThesisEvaluationQuestion(
                id=new_id(),
                mispricing_thesis_id=row.id,
                sort_order=idx,
                question_text=value,
            )
        )
    for idx, value in enumerate(output.permanent_loss_scenarios):
        session.add(
            MispricingThesisPermanentLossScenario(
                id=new_id(),
                mispricing_thesis_id=row.id,
                sort_order=idx,
                scenario_text=value,
            )
        )


def replace_evaluation_report(
    session: Session,
    execution: AgentExecution,
    output_json: str,
) -> None:
    output = EvaluationReportSchema.model_validate_json(output_json)
    existing = session.scalars(
        select(EvaluationReport).where(
            col(EvaluationReport.agent_execution_id) == execution.id
        )
    ).first()
    if existing is not None:
        session.exec(
            delete(EvaluationQuestionAssessment).where(
                col(EvaluationQuestionAssessment.evaluation_report_id) == existing.id
            )
        )
        session.exec(
            delete(EvaluationCaveat).where(
                col(EvaluationCaveat.evaluation_report_id) == existing.id
            )
        )
        session.delete(existing)
        session.flush()

    report = EvaluationReport(
        id=new_id(),
        agent_execution_id=execution.id,
        governance_concerns=output.red_flag_screen.governance_concerns,
        balance_sheet_stress=output.red_flag_screen.balance_sheet_stress,
        customer_or_supplier_concentration=output.red_flag_screen.customer_or_supplier_concentration,
        accounting_quality=output.red_flag_screen.accounting_quality,
        related_party_transactions=output.red_flag_screen.related_party_transactions,
        litigation_or_regulatory_risk=output.red_flag_screen.litigation_or_regulatory_risk,
        overall_red_flag_verdict=output.red_flag_screen.overall_red_flag_verdict.value,
        thesis_verdict=output.thesis_verdict.value,
        verdict_rationale=output.verdict_rationale,
        material_data_gaps=output.material_data_gaps,
    )
    session.add(report)
    for idx, qa in enumerate(output.question_assessments):
        session.add(
            EvaluationQuestionAssessment(
                id=new_id(),
                evaluation_report_id=report.id,
                sort_order=idx,
                question=qa.question,
                evidence=qa.evidence,
                verdict=qa.verdict,
                confidence=qa.confidence,
            )
        )
    for idx, caveat in enumerate(output.caveats):
        session.add(
            EvaluationCaveat(
                id=new_id(),
                evaluation_report_id=report.id,
                sort_order=idx,
                caveat=caveat,
            )
        )


def replace_appraiser_report(
    session: Session,
    execution: AgentExecution,
    output_json: str,
) -> None:
    output = AppraiserOutput.model_validate_json(output_json)
    existing = session.scalars(
        select(AppraiserReport).where(
            col(AppraiserReport.agent_execution_id) == execution.id
        )
    ).first()
    if existing is not None:
        session.delete(existing)
        session.flush()
    row = AppraiserReport(
        id=new_id(),
        agent_execution_id=execution.id,
        ebit=output.stock_data.ebit,
        revenue=output.stock_data.revenue,
        capital_expenditure=output.stock_data.capital_expenditure,
        n_shares_outstanding=output.stock_data.n_shares_outstanding,
        market_cap=output.stock_data.market_cap,
        gross_debt=output.stock_data.gross_debt,
        gross_debt_last_year=output.stock_data.gross_debt_last_year,
        net_debt=output.stock_data.net_debt,
        total_interest_expense=output.stock_data.total_interest_expense,
        beta=output.stock_data.beta,
        reasoning=output.stock_assumptions.reasoning,
        forecast_period_years=output.stock_assumptions.forecast_period_years,
        assumed_tax_rate=output.stock_assumptions.assumed_tax_rate,
        assumed_forecast_period_annual_revenue_growth_rate=output.stock_assumptions.assumed_forecast_period_annual_revenue_growth_rate,
        assumed_perpetuity_cash_flow_growth_rate=output.stock_assumptions.assumed_perpetuity_cash_flow_growth_rate,
        assumed_ebit_margin=output.stock_assumptions.assumed_ebit_margin,
        assumed_depreciation_and_amortization_rate=output.stock_assumptions.assumed_depreciation_and_amortization_rate,
        assumed_capex_rate=output.stock_assumptions.assumed_capex_rate,
        assumed_change_in_working_capital_rate=output.stock_assumptions.assumed_change_in_working_capital_rate,
    )
    session.add(row)


def upsert_run_final_decision(
    session: Session,
    *,
    run_id: str,
    source_agent_execution_id: str,
    decision_type: DecisionTypeDb,
    decision_date: date,
    is_existing_position: bool,
    rating: str,
    recommended_action: str,
    conviction: str | None,
    rejection_reason: str | None,
    current_price: float | None,
    bear_intrinsic_value: float | None,
    base_intrinsic_value: float | None,
    bull_intrinsic_value: float | None,
    margin_of_safety_base_pct: float | None,
    margin_of_safety_verdict: str | None,
    primary_driver: str | None,
    red_flag_disposition: str | None,
    data_gap_disposition: str | None,
    thesis_expiry_note: str | None,
    supporting_factors: list[str],
    mitigating_factors: list[str],
) -> None:
    existing = session.scalars(
        select(RunFinalDecision).where(col(RunFinalDecision.run_id) == run_id)
    ).first()
    if existing is not None:
        session.exec(
            delete(RunFinalDecisionSupportingFactor).where(
                col(RunFinalDecisionSupportingFactor.run_final_decision_id)
                == existing.id
            )
        )
        session.exec(
            delete(RunFinalDecisionMitigatingFactor).where(
                col(RunFinalDecisionMitigatingFactor.run_final_decision_id)
                == existing.id
            )
        )
        session.delete(existing)
        session.flush()

    row = RunFinalDecision(
        id=new_id(),
        run_id=run_id,
        source_agent_execution_id=source_agent_execution_id,
        decision_type=decision_type,
        decision_date=decision_date,
        is_existing_position=is_existing_position,
        rating=rating,
        recommended_action=recommended_action,
        conviction=conviction,
        rejection_reason=rejection_reason,
        current_price=current_price,
        bear_intrinsic_value=bear_intrinsic_value,
        base_intrinsic_value=base_intrinsic_value,
        bull_intrinsic_value=bull_intrinsic_value,
        margin_of_safety_base_pct=margin_of_safety_base_pct,
        margin_of_safety_verdict=margin_of_safety_verdict,
        primary_driver=primary_driver,
        red_flag_disposition=red_flag_disposition,
        data_gap_disposition=data_gap_disposition,
        thesis_expiry_note=thesis_expiry_note,
    )
    session.add(row)
    for idx, factor in enumerate(supporting_factors):
        session.add(
            RunFinalDecisionSupportingFactor(
                id=new_id(),
                run_final_decision_id=row.id,
                sort_order=idx,
                factor_text=factor,
            )
        )
    for idx, factor in enumerate(mitigating_factors):
        session.add(
            RunFinalDecisionMitigatingFactor(
                id=new_id(),
                run_final_decision_id=row.id,
                sort_order=idx,
                factor_text=factor,
            )
        )


def insert_dcf_valuation(
    session: Session,
    *,
    run_id: str,
    appraiser_agent_execution_id: str,
    dcf_result: DCFAnalysisResult,
) -> None:
    existing = session.scalars(
        select(DcfValuation).where(col(DcfValuation.run_id) == run_id)
    ).first()
    if existing is not None:
        session.delete(existing)
        session.flush()
    session.add(
        DcfValuation(
            id=new_id(),
            run_id=run_id,
            appraiser_agent_execution_id=appraiser_agent_execution_id,
            intrinsic_share_price=dcf_result.intrinsic_share_price,
            enterprise_value=dcf_result.enterprise_value,
            equity_value=dcf_result.equity_value,
        )
    )
