"""Persist structured agent outputs (research, thesis, evaluation, appraiser, verdicts)."""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Literal, cast

from sqlalchemy import delete, select
from sqlmodel import Session, col

from discount_analyst.adapters.persistence.crud.candidate_snapshots import (
    candidate_to_snapshot,
)
from discount_analyst.adapters.persistence.crud.db_utils import (
    new_id,
    require_lane_run_id,
)
from discount_analyst.adapters.persistence.models import (
    AgentExecution,
    AppraiserReport,
    CandidateSnapshot,
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
)
from discount_analyst.agents.appraiser.schema import (
    AppraiserOutput,
    ValuationMethodResult,
)
from discount_analyst.domain.valuation.intrinsic_value_distribution import (
    IntrinsicValueDistribution,
)
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


def persist_surveyor_output(
    session: Session,
    execution: AgentExecution,
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
            col(CandidateSnapshot.agent_execution_id) == execution.id
        )
    )
    for idx, candidate in enumerate(candidates):
        session.add(
            candidate_to_snapshot(
                candidate=candidate,
                sort_order=idx,
                agent_execution_id=execution.id,
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
        agent_execution_id=execution.id,
    )
    session.add(snap)
    run = session.get(Run, require_lane_run_id(execution))
    if run is not None:
        run.candidate_snapshot_id = snap.id
        run.company_name = output.candidate.company_name


def replace_research_report(
    session: Session,
    execution: AgentExecution,
    output_json: str,
) -> None:
    output = DeepResearchReport.model_validate_json(output_json)
    run = session.get(Run, require_lane_run_id(execution))
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


def appraiser_output_from_report(row: AppraiserReport) -> AppraiserOutput:
    return AppraiserOutput(
        ticker=row.ticker,
        company_name=row.company_name,
        valuation_date=row.valuation_date,
        summary=row.summary,
        valuation_distribution=IntrinsicValueDistribution(
            currency=row.currency,
            current_share_price=row.current_share_price,
            expected_intrinsic_value=row.expected_intrinsic_value,
            p10_intrinsic_value=row.p10_intrinsic_value,
            p25_intrinsic_value=row.p25_intrinsic_value,
            p50_intrinsic_value=row.p50_intrinsic_value,
            p75_intrinsic_value=row.p75_intrinsic_value,
            p90_intrinsic_value=row.p90_intrinsic_value,
            distribution_method=row.distribution_method,
            distribution_reasoning=row.distribution_reasoning,
        ),
        methods=[
            ValuationMethodResult.model_validate(method)
            for method in json.loads(row.methods_json)
        ],
        key_value_drivers=json.loads(row.key_value_drivers_json),
        downside_risks_to_value=json.loads(row.downside_risks_to_value_json),
        upside_drivers_to_value=json.loads(row.upside_drivers_to_value_json),
        data_quality=cast(Literal["High", "Medium", "Low"], row.data_quality),
        caveats=json.loads(row.caveats_json),
    )


def replace_appraiser_output(
    session: Session,
    execution: AgentExecution,
    output_json: str,
) -> None:
    output = AppraiserOutput.model_validate_json(output_json)
    distribution = output.valuation_distribution
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
        ticker=output.ticker,
        company_name=output.company_name,
        valuation_date=output.valuation_date,
        summary=output.summary,
        currency=distribution.currency,
        current_share_price=distribution.current_share_price,
        expected_intrinsic_value=distribution.expected_intrinsic_value,
        p10_intrinsic_value=distribution.p10_intrinsic_value,
        p25_intrinsic_value=distribution.p25_intrinsic_value,
        p50_intrinsic_value=distribution.p50_intrinsic_value,
        p75_intrinsic_value=distribution.p75_intrinsic_value,
        p90_intrinsic_value=distribution.p90_intrinsic_value,
        distribution_method=distribution.distribution_method,
        distribution_reasoning=distribution.distribution_reasoning,
        methods_json=json.dumps(
            [method.model_dump(mode="json") for method in output.methods],
            separators=(",", ":"),
        ),
        key_value_drivers_json=json.dumps(
            output.key_value_drivers, separators=(",", ":")
        ),
        downside_risks_to_value_json=json.dumps(
            output.downside_risks_to_value, separators=(",", ":")
        ),
        upside_drivers_to_value_json=json.dumps(
            output.upside_drivers_to_value, separators=(",", ":")
        ),
        data_quality=output.data_quality,
        caveats_json=json.dumps(output.caveats, separators=(",", ":")),
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
