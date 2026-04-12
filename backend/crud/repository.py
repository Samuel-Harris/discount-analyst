"""CRUD helpers for dashboard workflows (SQLModel session operations)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime
from typing import Any

from pydantic_ai import ModelMessagesTypeAdapter
from sqlalchemy import case, func
from sqlmodel import Session, delete, select

from backend.db.models import (
    AgentConversation,
    AgentConversationMessage,
    AgentConversationMessagePart,
    AgentExecution,
    AgentNameDb,
    AppraiserReport,
    CandidateSnapshot,
    DcfValuation,
    DecisionTypeDb,
    EntryPathDb,
    EvaluationCaveat,
    EvaluationQuestionAssessment,
    EvaluationReport,
    ExecutionStatusDb,
    MessageKindDb,
    MessagePartKindDb,
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
    WorkflowRun,
    WorkflowRunPortfolioTicker,
    WorkflowRunStatusDb,
)
from discount_analyst.agents.appraiser.schema import AppraiserOutput
from discount_analyst.agents.arbiter.schema import (
    ArbiterDecision,
    ArbiterRationale,
    MarginOfSafetyAssessment,
)
from discount_analyst.agents.profiler.schema import ProfilerOutput
from discount_analyst.agents.researcher.schema import (
    BusinessModel,
    DataGapsUpdate,
    DeepResearchReport,
    FinancialProfile,
    ManagementAssessment,
    MarketNarrative,
)
from discount_analyst.agents.sentinel.schema import (
    EvaluationReport as EvaluationReportSchema,
    OverallRedFlagVerdict,
    QuestionAssessment,
    RedFlagScreen,
    ThesisVerdict,
)
from discount_analyst.agents.strategist.schema import (
    MispricingThesis as MispricingThesisSchema,
)
from discount_analyst.agents.surveyor.schema import (
    KeyMetrics,
    SurveyorCandidate,
    SurveyorOutput,
)
from discount_analyst.pipeline.schema import SentinelRejection, Verdict
from discount_analyst.valuation.data_types import DCFAnalysisResult
from discount_analyst.valuation.schema import StockAssumptions, StockData


def new_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_iso() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def _dump_json_string(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


_TERMINAL_EXEC = frozenset(
    {
        ExecutionStatusDb.COMPLETED.value,
        ExecutionStatusDb.SKIPPED.value,
        ExecutionStatusDb.REJECTED.value,
        ExecutionStatusDb.FAILED.value,
    }
)
_ACTIVE_EXEC = frozenset(
    {
        ExecutionStatusDb.PENDING.value,
        ExecutionStatusDb.RUNNING.value,
    }
)


def _message_part_kind_from_raw(raw: str) -> MessagePartKindDb:
    mapping = {
        "system-prompt": MessagePartKindDb.SYSTEM_PROMPT,
        "user-prompt": MessagePartKindDb.USER_PROMPT,
        "text": MessagePartKindDb.TEXT,
        "tool-call": MessagePartKindDb.TOOL_CALL,
        "tool-return": MessagePartKindDb.TOOL_RETURN,
        "retry-prompt": MessagePartKindDb.RETRY_PROMPT,
    }
    return mapping[raw]


def _message_part_kind_to_raw(kind: MessagePartKindDb) -> str:
    mapping = {
        MessagePartKindDb.SYSTEM_PROMPT: "system-prompt",
        MessagePartKindDb.USER_PROMPT: "user-prompt",
        MessagePartKindDb.TEXT: "text",
        MessagePartKindDb.TOOL_CALL: "tool-call",
        MessagePartKindDb.TOOL_RETURN: "tool-return",
        MessagePartKindDb.RETRY_PROMPT: "retry-prompt",
    }
    return mapping[kind]


def _candidate_to_snapshot(
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


def _snapshot_to_candidate(snapshot: CandidateSnapshot) -> SurveyorCandidate:
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


def _parse_messages_payload(
    *,
    messages: list[object] | None,
    messages_json: str | None,
) -> list[dict[str, Any]]:
    if messages is not None:
        return ModelMessagesTypeAdapter.dump_python(messages, mode="json")
    if messages_json:
        loaded = json.loads(messages_json)
        if isinstance(loaded, list):
            return loaded
    return []


def _replace_conversation_messages(
    session: Session,
    *,
    conversation_id: str,
    messages_payload: list[dict[str, Any]],
) -> None:
    existing_messages = list(
        session.exec(
            select(AgentConversationMessage).where(
                AgentConversationMessage.conversation_id == conversation_id
            )
        )
    )
    for msg in existing_messages:
        session.exec(
            delete(AgentConversationMessagePart).where(
                AgentConversationMessagePart.conversation_message_id == msg.id
            )
        )
    session.exec(
        delete(AgentConversationMessage).where(
            AgentConversationMessage.conversation_id == conversation_id
        )
    )

    for message_index, message_obj in enumerate(messages_payload):
        msg_kind_raw = str(message_obj.get("kind", "request"))
        msg_kind = (
            MessageKindDb.REQUEST
            if msg_kind_raw == "request"
            else MessageKindDb.RESPONSE
        )
        msg_row = AgentConversationMessage(
            id=new_id(),
            conversation_id=conversation_id,
            message_index=message_index,
            message_kind=msg_kind,
        )
        session.add(msg_row)
        parts = message_obj.get("parts", [])
        if not isinstance(parts, list):
            continue
        for part_index, part_obj in enumerate(parts):
            if not isinstance(part_obj, dict):
                continue
            raw_kind = str(part_obj.get("part_kind", "text"))
            kind = _message_part_kind_from_raw(raw_kind)
            content_text: str | None = None
            if kind == MessagePartKindDb.TOOL_CALL:
                content_text = _dump_json_string(part_obj.get("args", ""))
            elif "content" in part_obj:
                content_text = _dump_json_string(part_obj.get("content"))

            part_row = AgentConversationMessagePart(
                id=new_id(),
                conversation_message_id=msg_row.id,
                part_index=part_index,
                part_kind=kind,
                content_text=content_text,
                tool_name=part_obj.get("tool_name"),
                tool_call_id=part_obj.get("tool_call_id"),
            )
            session.add(part_row)


def _build_messages_json(session: Session, conversation_id: str) -> str:
    msg_rows = list(
        session.exec(
            select(AgentConversationMessage)
            .where(AgentConversationMessage.conversation_id == conversation_id)
            .order_by(AgentConversationMessage.message_index)
        )
    )
    out: list[dict[str, Any]] = []
    for msg_row in msg_rows:
        parts_rows = list(
            session.exec(
                select(AgentConversationMessagePart)
                .where(
                    AgentConversationMessagePart.conversation_message_id == msg_row.id
                )
                .order_by(AgentConversationMessagePart.part_index)
            )
        )
        parts: list[dict[str, Any]] = []
        for part_row in parts_rows:
            raw_kind = _message_part_kind_to_raw(part_row.part_kind)
            part: dict[str, Any] = {"part_kind": raw_kind}
            if part_row.part_kind == MessagePartKindDb.TOOL_CALL:
                part["tool_name"] = part_row.tool_name
                part["tool_call_id"] = part_row.tool_call_id
                part["args"] = part_row.content_text or ""
            elif part_row.part_kind == MessagePartKindDb.TOOL_RETURN:
                part["tool_name"] = part_row.tool_name
                part["tool_call_id"] = part_row.tool_call_id
                part["content"] = part_row.content_text or ""
            else:
                part["content"] = part_row.content_text or ""
                if part_row.tool_name is not None:
                    part["tool_name"] = part_row.tool_name
                if part_row.tool_call_id is not None:
                    part["tool_call_id"] = part_row.tool_call_id
            parts.append(part)

        out.append(
            {
                "kind": msg_row.message_kind.value,
                "parts": parts,
            }
        )
    return json.dumps(out, separators=(",", ":"), ensure_ascii=False)


def _persist_surveyor_output(
    session: Session,
    execution: WorkflowAgentExecution,
    output_json: str,
) -> None:
    raw = json.loads(output_json)
    candidates_raw = raw.get("candidates", []) if isinstance(raw, dict) else []
    candidates = [SurveyorCandidate.model_validate(c) for c in candidates_raw]
    session.exec(
        delete(CandidateSnapshot).where(
            CandidateSnapshot.workflow_agent_execution_id == execution.id
        )
    )
    for idx, candidate in enumerate(candidates):
        session.add(
            _candidate_to_snapshot(
                candidate=candidate,
                sort_order=idx,
                workflow_agent_execution_id=execution.id,
                agent_execution_id=None,
            )
        )


def _persist_profiler_output(
    session: Session,
    execution: AgentExecution,
    output_json: str,
) -> None:
    output = ProfilerOutput.model_validate_json(output_json)
    session.exec(
        delete(CandidateSnapshot).where(
            CandidateSnapshot.agent_execution_id == execution.id
        )
    )
    snap = _candidate_to_snapshot(
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


def _replace_research_report(
    session: Session,
    execution: AgentExecution,
    output_json: str,
) -> None:
    output = DeepResearchReport.model_validate_json(output_json)
    run = session.get(Run, execution.run_id)
    if run is None or run.candidate_snapshot_id is None:
        return
    existing = session.exec(
        select(ResearchReport).where(ResearchReport.agent_execution_id == execution.id)
    ).first()
    if existing is not None:
        session.exec(
            delete(ResearchReportNarrativeMonitoringSignal).where(
                ResearchReportNarrativeMonitoringSignal.research_report_id
                == existing.id
            )
        )
        session.exec(
            delete(ResearchReportRisk).where(
                ResearchReportRisk.research_report_id == existing.id
            )
        )
        session.exec(
            delete(ResearchReportPotentialCatalyst).where(
                ResearchReportPotentialCatalyst.research_report_id == existing.id
            )
        )
        session.exec(
            delete(ResearchReportClosedGap).where(
                ResearchReportClosedGap.research_report_id == existing.id
            )
        )
        session.exec(
            delete(ResearchReportRemainingOpenGap).where(
                ResearchReportRemainingOpenGap.research_report_id == existing.id
            )
        )
        session.exec(
            delete(ResearchReportMaterialOpenGap).where(
                ResearchReportMaterialOpenGap.research_report_id == existing.id
            )
        )
        session.exec(
            delete(ResearchReportSourceNote).where(
                ResearchReportSourceNote.research_report_id == existing.id
            )
        )
        session.delete(existing)

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


def _replace_mispricing_thesis(
    session: Session,
    execution: AgentExecution,
    output_json: str,
) -> None:
    output = MispricingThesisSchema.model_validate_json(output_json)
    existing = session.exec(
        select(MispricingThesis).where(
            MispricingThesis.agent_execution_id == execution.id
        )
    ).first()
    if existing is not None:
        session.exec(
            delete(MispricingThesisFalsificationCondition).where(
                MispricingThesisFalsificationCondition.mispricing_thesis_id
                == existing.id
            )
        )
        session.exec(
            delete(MispricingThesisRisk).where(
                MispricingThesisRisk.mispricing_thesis_id == existing.id
            )
        )
        session.exec(
            delete(MispricingThesisEvaluationQuestion).where(
                MispricingThesisEvaluationQuestion.mispricing_thesis_id == existing.id
            )
        )
        session.exec(
            delete(MispricingThesisPermanentLossScenario).where(
                MispricingThesisPermanentLossScenario.mispricing_thesis_id
                == existing.id
            )
        )
        session.delete(existing)
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


def _replace_evaluation_report(
    session: Session,
    execution: AgentExecution,
    output_json: str,
) -> None:
    output = EvaluationReportSchema.model_validate_json(output_json)
    existing = session.exec(
        select(EvaluationReport).where(
            EvaluationReport.agent_execution_id == execution.id
        )
    ).first()
    if existing is not None:
        session.exec(
            delete(EvaluationQuestionAssessment).where(
                EvaluationQuestionAssessment.evaluation_report_id == existing.id
            )
        )
        session.exec(
            delete(EvaluationCaveat).where(
                EvaluationCaveat.evaluation_report_id == existing.id
            )
        )
        session.delete(existing)

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


def _replace_appraiser_report(
    session: Session,
    execution: AgentExecution,
    output_json: str,
) -> None:
    output = AppraiserOutput.model_validate_json(output_json)
    existing = session.exec(
        select(AppraiserReport).where(
            AppraiserReport.agent_execution_id == execution.id
        )
    ).first()
    if existing is not None:
        session.delete(existing)
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


def _upsert_run_final_decision(
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
    existing = session.exec(
        select(RunFinalDecision).where(RunFinalDecision.run_id == run_id)
    ).first()
    if existing is not None:
        session.exec(
            delete(RunFinalDecisionSupportingFactor).where(
                RunFinalDecisionSupportingFactor.run_final_decision_id == existing.id
            )
        )
        session.exec(
            delete(RunFinalDecisionMitigatingFactor).where(
                RunFinalDecisionMitigatingFactor.run_final_decision_id == existing.id
            )
        )
        session.delete(existing)

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
    existing = session.exec(
        select(DcfValuation).where(DcfValuation.run_id == run_id)
    ).first()
    if existing is not None:
        session.delete(existing)
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
    session.commit()


def get_workflow_run_inputs(
    session: Session, workflow_run_id: str
) -> tuple[list[str], bool] | None:
    wf = session.get(WorkflowRun, workflow_run_id)
    if wf is None:
        return None
    tickers = list(
        session.exec(
            select(WorkflowRunPortfolioTicker)
            .where(WorkflowRunPortfolioTicker.workflow_run_id == workflow_run_id)
            .order_by(WorkflowRunPortfolioTicker.sort_order)
        )
    )
    return [t.ticker for t in tickers], wf.is_mock


def list_profiler_runs_for_workflow(
    session: Session, workflow_run_id: str
) -> list[tuple[str, str]]:
    rows = list(
        session.exec(
            select(Run)
            .where(
                Run.workflow_run_id == workflow_run_id,
                Run.entry_path == EntryPathDb.PROFILER,
            )
            .order_by(Run.started_at)
        )
    )
    return [(row.id, row.ticker) for row in rows]


def recompute_workflow_status(session: Session, workflow_run_id: str) -> None:
    wf = session.get(WorkflowRun, workflow_run_id)
    if wf is None:
        return

    surveyor = session.exec(
        select(WorkflowAgentExecution).where(
            WorkflowAgentExecution.workflow_run_id == workflow_run_id,
            WorkflowAgentExecution.agent_name == AgentNameDb.SURVEYOR,
        )
    ).first()
    runs = list(
        session.exec(select(Run.status).where(Run.workflow_run_id == workflow_run_id))
    )

    new_status: WorkflowRunStatusDb | None = None
    if surveyor is None:
        new_status = WorkflowRunStatusDb.RUNNING
    elif surveyor.status.value == ExecutionStatusDb.FAILED.value:
        new_status = WorkflowRunStatusDb.FAILED
    elif surveyor.status.value in _ACTIVE_EXEC:
        new_status = WorkflowRunStatusDb.RUNNING
    elif not runs:
        if surveyor.status.value in _TERMINAL_EXEC:
            new_status = WorkflowRunStatusDb.COMPLETED
    else:
        statuses = [status.value for status in runs]
        if WorkflowRunStatusDb.FAILED.value in statuses:
            new_status = WorkflowRunStatusDb.FAILED
        elif WorkflowRunStatusDb.RUNNING.value in statuses:
            new_status = WorkflowRunStatusDb.RUNNING
        elif all(s == WorkflowRunStatusDb.COMPLETED.value for s in statuses):
            new_status = WorkflowRunStatusDb.COMPLETED
        else:
            new_status = WorkflowRunStatusDb.RUNNING

    if new_status is None:
        return

    wf.status = new_status
    if new_status == WorkflowRunStatusDb.RUNNING:
        wf.completed_at = None
    else:
        wf.completed_at = utc_now()
    session.add(wf)
    session.commit()


def insert_workflow_run(
    session: Session,
    *,
    workflow_run_id: str,
    portfolio_tickers: list[str],
    is_mock: bool,
) -> None:
    session.add(
        WorkflowRun(
            id=workflow_run_id,
            started_at=utc_now(),
            completed_at=None,
            status=WorkflowRunStatusDb.RUNNING,
            is_mock=is_mock,
            error_message=None,
        )
    )
    for idx, ticker in enumerate(portfolio_tickers):
        session.add(
            WorkflowRunPortfolioTicker(
                id=new_id(),
                workflow_run_id=workflow_run_id,
                sort_order=idx,
                ticker=ticker,
            )
        )
    session.commit()


def insert_surveyor_workflow_execution(
    session: Session,
    *,
    execution_id: str,
    workflow_run_id: str,
) -> None:
    session.add(
        WorkflowAgentExecution(
            id=execution_id,
            workflow_run_id=workflow_run_id,
            agent_name=AgentNameDb.SURVEYOR,
            status=ExecutionStatusDb.PENDING,
            started_at=None,
            completed_at=None,
            error_message=None,
        )
    )
    session.commit()


PROFILER_ENTRY_AGENT_NAMES = (
    "profiler",
    "researcher",
    "strategist",
    "sentinel",
    "appraiser",
    "arbiter",
)
SURVEYOR_ENTRY_AGENT_NAMES = (
    "researcher",
    "strategist",
    "sentinel",
    "appraiser",
    "arbiter",
)


def insert_ticker_run_with_agents(
    session: Session,
    *,
    run_id: str,
    workflow_run_id: str,
    ticker: str,
    company_name: str,
    entry_path: str,
    is_existing_position: bool,
    is_mock: bool,
    agent_names: tuple[str, ...],
    candidate_snapshot_id: str | None = None,
) -> None:
    session.add(
        Run(
            id=run_id,
            workflow_run_id=workflow_run_id,
            candidate_snapshot_id=candidate_snapshot_id,
            ticker=ticker,
            company_name=company_name,
            started_at=utc_now(),
            completed_at=None,
            entry_path=EntryPathDb(entry_path),
            is_existing_position=is_existing_position,
            status=WorkflowRunStatusDb.RUNNING,
            is_mock=is_mock,
            error_message=None,
            final_rating=None,
            decision_type=None,
            recommended_action=None,
        )
    )
    for name in agent_names:
        session.add(
            AgentExecution(
                id=new_id(),
                run_id=run_id,
                agent_name=AgentNameDb(name),
                status=ExecutionStatusDb.PENDING,
                started_at=None,
                completed_at=None,
                error_message=None,
            )
        )
    session.commit()


def get_agent_execution_id_by_run_and_agent(
    session: Session,
    *,
    run_id: str,
    agent_name: str,
) -> str | None:
    row = session.exec(
        select(AgentExecution.id).where(
            AgentExecution.run_id == run_id,
            AgentExecution.agent_name == AgentNameDb(agent_name),
        )
    ).first()
    return row


def get_workflow_surveyor_execution_id(
    session: Session, workflow_run_id: str
) -> str | None:
    row = session.exec(
        select(WorkflowAgentExecution.id).where(
            WorkflowAgentExecution.workflow_run_id == workflow_run_id,
            WorkflowAgentExecution.agent_name == AgentNameDb.SURVEYOR,
        )
    ).first()
    return row


def get_workflow_candidate_snapshot_id(
    session: Session, *, workflow_execution_id: str, ticker: str
) -> str | None:
    row = session.exec(
        select(CandidateSnapshot.id).where(
            CandidateSnapshot.workflow_agent_execution_id == workflow_execution_id,
            CandidateSnapshot.ticker == ticker,
        )
    ).first()
    return row


def update_workflow_agent_execution(
    session: Session,
    *,
    execution_id: str,
    status: str,
    output_json: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
    error_message: str | None = None,
) -> None:
    execution = session.get(WorkflowAgentExecution, execution_id)
    if execution is None:
        return
    execution.status = ExecutionStatusDb(status)
    if started_at is not None:
        execution.started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    if completed_at is not None:
        execution.completed_at = datetime.fromisoformat(
            completed_at.replace("Z", "+00:00")
        )
    if error_message is not None:
        execution.error_message = error_message

    if output_json and execution.agent_name == AgentNameDb.SURVEYOR:
        _persist_surveyor_output(session, execution, output_json)
    session.add(execution)
    session.commit()


def update_agent_execution(
    session: Session,
    *,
    execution_id: str,
    status: str,
    output_json: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
    error_message: str | None = None,
) -> None:
    execution = session.get(AgentExecution, execution_id)
    if execution is None:
        return
    execution.status = ExecutionStatusDb(status)
    if started_at is not None:
        execution.started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    if completed_at is not None:
        execution.completed_at = datetime.fromisoformat(
            completed_at.replace("Z", "+00:00")
        )
    if error_message is not None:
        execution.error_message = error_message

    if output_json:
        match execution.agent_name:
            case AgentNameDb.PROFILER:
                _persist_profiler_output(session, execution, output_json)
            case AgentNameDb.RESEARCHER:
                _replace_research_report(session, execution, output_json)
            case AgentNameDb.STRATEGIST:
                _replace_mispricing_thesis(session, execution, output_json)
            case AgentNameDb.SENTINEL:
                _replace_evaluation_report(session, execution, output_json)
            case AgentNameDb.APPRAISER:
                _replace_appraiser_report(session, execution, output_json)
            case _:
                pass
    session.add(execution)
    session.commit()


def update_ticker_run_completion(
    session: Session,
    *,
    run_id: str,
    status: str,
    final_rating: str | None,
    decision_type: str | None,
    recommended_action: str | None,
    final_verdict_json: str | None,
    error_message: str | None = None,
) -> None:
    run = session.get(Run, run_id)
    if run is None:
        return
    run.status = WorkflowRunStatusDb(status)
    run.completed_at = utc_now()
    run.final_rating = final_rating
    run.decision_type = DecisionTypeDb(decision_type) if decision_type else None
    run.recommended_action = recommended_action
    run.error_message = error_message
    session.add(run)

    if final_verdict_json and decision_type:
        verdict = Verdict.model_validate_json(final_verdict_json)
        if decision_type == DecisionTypeDb.ARBITER.value:
            source_execution_id = get_agent_execution_id_by_run_and_agent(
                session, run_id=run_id, agent_name=AgentNameDb.ARBITER.value
            )
            if source_execution_id is None:
                session.commit()
                return
            decision = ArbiterDecision.model_validate(verdict.decision)
            _upsert_run_final_decision(
                session,
                run_id=run_id,
                source_agent_execution_id=source_execution_id,
                decision_type=DecisionTypeDb.ARBITER,
                decision_date=date.fromisoformat(decision.decision_date),
                is_existing_position=decision.is_existing_position,
                rating=decision.rating.value,
                recommended_action=decision.recommended_action,
                conviction=decision.conviction,
                rejection_reason=None,
                current_price=decision.margin_of_safety.current_price,
                bear_intrinsic_value=decision.margin_of_safety.bear_intrinsic_value,
                base_intrinsic_value=decision.margin_of_safety.base_intrinsic_value,
                bull_intrinsic_value=decision.margin_of_safety.bull_intrinsic_value,
                margin_of_safety_base_pct=decision.margin_of_safety.margin_of_safety_base_pct,
                margin_of_safety_verdict=decision.margin_of_safety.margin_of_safety_verdict,
                primary_driver=decision.rationale.primary_driver,
                red_flag_disposition=decision.rationale.red_flag_disposition,
                data_gap_disposition=decision.rationale.data_gap_disposition,
                thesis_expiry_note=decision.thesis_expiry_note,
                supporting_factors=decision.rationale.supporting_factors,
                mitigating_factors=decision.rationale.mitigating_factors,
            )
        elif decision_type == DecisionTypeDb.SENTINEL_REJECTION.value:
            source_execution_id = get_agent_execution_id_by_run_and_agent(
                session, run_id=run_id, agent_name=AgentNameDb.SENTINEL.value
            )
            if source_execution_id is None:
                session.commit()
                return
            decision = SentinelRejection.model_validate(verdict.decision)
            _upsert_run_final_decision(
                session,
                run_id=run_id,
                source_agent_execution_id=source_execution_id,
                decision_type=DecisionTypeDb.SENTINEL_REJECTION,
                decision_date=date.fromisoformat(decision.decision_date),
                is_existing_position=decision.is_existing_position,
                rating=decision.rating.value,
                recommended_action=decision.recommended_action,
                conviction=None,
                rejection_reason=decision.rejection_reason,
                current_price=None,
                bear_intrinsic_value=None,
                base_intrinsic_value=None,
                bull_intrinsic_value=None,
                margin_of_safety_base_pct=None,
                margin_of_safety_verdict=None,
                primary_driver=None,
                red_flag_disposition=None,
                data_gap_disposition=None,
                thesis_expiry_note=None,
                supporting_factors=[],
                mitigating_factors=[],
            )

    session.commit()


def update_ticker_run_company_name(
    session: Session, *, run_id: str, company_name: str
) -> None:
    run = session.get(Run, run_id)
    if run is None:
        return
    run.company_name = company_name
    session.add(run)
    session.commit()


def insert_conversation_for_workflow_agent(
    session: Session,
    *,
    conversation_id: str,
    workflow_agent_execution_id: str,
    system_prompt: str,
    messages_json: str | None = None,
    assistant_response: str | None = None,
    messages: list[object] | None = None,
) -> None:
    del assistant_response
    existing = session.exec(
        select(AgentConversation).where(
            AgentConversation.workflow_agent_execution_id == workflow_agent_execution_id
        )
    ).first()
    if existing is not None:
        conversation_id = existing.id
        existing.system_prompt = system_prompt
        session.add(existing)
    else:
        session.add(
            AgentConversation(
                id=conversation_id,
                workflow_agent_execution_id=workflow_agent_execution_id,
                agent_execution_id=None,
                system_prompt=system_prompt,
            )
        )
    payload = _parse_messages_payload(messages=messages, messages_json=messages_json)
    _replace_conversation_messages(
        session, conversation_id=conversation_id, messages_payload=payload
    )
    session.commit()


def insert_conversation_for_agent_execution(
    session: Session,
    *,
    conversation_id: str,
    agent_execution_id: str,
    system_prompt: str,
    messages_json: str | None = None,
    assistant_response: str | None = None,
    messages: list[object] | None = None,
) -> None:
    del assistant_response
    existing = session.exec(
        select(AgentConversation).where(
            AgentConversation.agent_execution_id == agent_execution_id
        )
    ).first()
    if existing is not None:
        conversation_id = existing.id
        existing.system_prompt = system_prompt
        session.add(existing)
    else:
        session.add(
            AgentConversation(
                id=conversation_id,
                workflow_agent_execution_id=None,
                agent_execution_id=agent_execution_id,
                system_prompt=system_prompt,
            )
        )
    payload = _parse_messages_payload(messages=messages, messages_json=messages_json)
    _replace_conversation_messages(
        session, conversation_id=conversation_id, messages_payload=payload
    )
    session.commit()


def list_workflow_runs(session: Session) -> list[dict[str, Any]]:
    stmt = (
        select(
            WorkflowRun.id,
            WorkflowRun.started_at,
            WorkflowRun.completed_at,
            WorkflowRun.status,
            WorkflowRun.is_mock,
            WorkflowRun.error_message,
            func.count(Run.id),
            func.sum(case((Run.status == WorkflowRunStatusDb.COMPLETED, 1), else_=0)),
            func.sum(case((Run.status == WorkflowRunStatusDb.FAILED, 1), else_=0)),
        )
        .select_from(WorkflowRun)
        .join(Run, Run.workflow_run_id == WorkflowRun.id, isouter=True)
        .group_by(WorkflowRun.id)
        .order_by(WorkflowRun.started_at.desc())
    )
    rows = list(session.exec(stmt))
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "id": r[0],
                "started_at": r[1],
                "completed_at": r[2],
                "status": r[3].value,
                "is_mock": bool(r[4]),
                "error_message": r[5],
                "ticker_run_count": int(r[6] or 0),
                "completed_ticker_run_count": int(r[7] or 0),
                "failed_ticker_run_count": int(r[8] or 0),
            }
        )
    return out


def get_workflow_run_row(
    session: Session, workflow_run_id: str
) -> dict[str, Any] | None:
    wf = session.get(WorkflowRun, workflow_run_id)
    if wf is None:
        return None
    tickers = list(
        session.exec(
            select(WorkflowRunPortfolioTicker)
            .where(WorkflowRunPortfolioTicker.workflow_run_id == workflow_run_id)
            .order_by(WorkflowRunPortfolioTicker.sort_order)
        )
    )
    return {
        "id": wf.id,
        "started_at": wf.started_at,
        "completed_at": wf.completed_at,
        "status": wf.status.value,
        "is_mock": wf.is_mock,
        "error_message": wf.error_message,
        "portfolio_tickers": [t.ticker for t in tickers],
    }


def fetch_workflow_detail(
    session: Session, workflow_run_id: str
) -> dict[str, Any] | None:
    wf = get_workflow_run_row(session, workflow_run_id)
    if wf is None:
        return None

    se = session.exec(
        select(WorkflowAgentExecution).where(
            WorkflowAgentExecution.workflow_run_id == workflow_run_id,
            WorkflowAgentExecution.agent_name == AgentNameDb.SURVEYOR,
        )
    ).first()
    surveyor_execution = None
    if se is not None:
        surveyor_execution = {
            "id": se.id,
            "agent_name": se.agent_name.value,
            "status": se.status.value,
            "started_at": se.started_at,
            "completed_at": se.completed_at,
        }

    agent_order = {
        AgentNameDb.PROFILER.value: 0,
        AgentNameDb.RESEARCHER.value: 1,
        AgentNameDb.STRATEGIST.value: 2,
        AgentNameDb.SENTINEL.value: 3,
        AgentNameDb.APPRAISER.value: 4,
        AgentNameDb.ARBITER.value: 5,
    }

    runs = list(
        session.exec(
            select(Run)
            .where(Run.workflow_run_id == workflow_run_id)
            .order_by(Run.started_at)
        )
    )
    runs_out: list[dict[str, Any]] = []
    for rr in runs:
        agents = list(
            session.exec(select(AgentExecution).where(AgentExecution.run_id == rr.id))
        )
        agents_sorted = sorted(
            agents, key=lambda a: agent_order.get(a.agent_name.value, 99)
        )
        runs_out.append(
            {
                "id": rr.id,
                "ticker": rr.ticker,
                "company_name": rr.company_name,
                "entry_path": rr.entry_path.value,
                "status": rr.status.value,
                "final_rating": rr.final_rating,
                "decision_type": rr.decision_type.value if rr.decision_type else None,
                "agent_executions": [
                    {
                        "id": a.id,
                        "agent_name": a.agent_name.value,
                        "status": a.status.value,
                        "started_at": a.started_at,
                        "completed_at": a.completed_at,
                    }
                    for a in agents_sorted
                ],
            }
        )

    wf["surveyor_execution"] = surveyor_execution
    wf["runs"] = runs_out
    return wf


def _assistant_response_for_workflow_execution(
    session: Session, execution: WorkflowAgentExecution
) -> str:
    snapshots = list(
        session.exec(
            select(CandidateSnapshot)
            .where(CandidateSnapshot.workflow_agent_execution_id == execution.id)
            .order_by(CandidateSnapshot.sort_order)
        )
    )
    output = SurveyorOutput.model_construct(
        candidates=[_snapshot_to_candidate(s) for s in snapshots]
    )
    return output.model_dump_json()


def _assistant_response_for_run_agent(
    session: Session, execution: AgentExecution
) -> str:
    if execution.agent_name == AgentNameDb.PROFILER:
        snapshot = session.exec(
            select(CandidateSnapshot).where(
                CandidateSnapshot.agent_execution_id == execution.id
            )
        ).first()
        if snapshot is None:
            return "{}"
        return ProfilerOutput(
            candidate=_snapshot_to_candidate(snapshot)
        ).model_dump_json()

    if execution.agent_name == AgentNameDb.RESEARCHER:
        report = session.exec(
            select(ResearchReport).where(
                ResearchReport.agent_execution_id == execution.id
            )
        ).first()
        if report is None:
            return "{}"
        snapshot = session.get(CandidateSnapshot, report.candidate_snapshot_id)
        if snapshot is None:
            return "{}"
        narrative_signals = [
            r.signal
            for r in session.exec(
                select(ResearchReportNarrativeMonitoringSignal)
                .where(
                    ResearchReportNarrativeMonitoringSignal.research_report_id
                    == report.id
                )
                .order_by(ResearchReportNarrativeMonitoringSignal.sort_order)
            )
        ]
        risks = [
            r.risk
            for r in session.exec(
                select(ResearchReportRisk)
                .where(ResearchReportRisk.research_report_id == report.id)
                .order_by(ResearchReportRisk.sort_order)
            )
        ]
        catalysts = [
            r.catalyst
            for r in session.exec(
                select(ResearchReportPotentialCatalyst)
                .where(ResearchReportPotentialCatalyst.research_report_id == report.id)
                .order_by(ResearchReportPotentialCatalyst.sort_order)
            )
        ]
        closed_gaps = [
            r.gap_text
            for r in session.exec(
                select(ResearchReportClosedGap)
                .where(ResearchReportClosedGap.research_report_id == report.id)
                .order_by(ResearchReportClosedGap.sort_order)
            )
        ]
        remaining_open_gaps = [
            r.gap_text
            for r in session.exec(
                select(ResearchReportRemainingOpenGap)
                .where(ResearchReportRemainingOpenGap.research_report_id == report.id)
                .order_by(ResearchReportRemainingOpenGap.sort_order)
            )
        ]
        material_open_gaps = [
            r.gap_text
            for r in session.exec(
                select(ResearchReportMaterialOpenGap)
                .where(ResearchReportMaterialOpenGap.research_report_id == report.id)
                .order_by(ResearchReportMaterialOpenGap.sort_order)
            )
        ]
        source_notes = [
            r.source_note
            for r in session.exec(
                select(ResearchReportSourceNote)
                .where(ResearchReportSourceNote.research_report_id == report.id)
                .order_by(ResearchReportSourceNote.sort_order)
            )
        ]
        payload = DeepResearchReport(
            candidate=_snapshot_to_candidate(snapshot),
            executive_overview=report.executive_overview,
            business_model=BusinessModel(
                products_and_services=report.products_and_services,
                customer_segments=report.customer_segments,
                unit_economics=report.unit_economics,
                competitive_positioning=report.competitive_positioning,
                moat_and_durability=report.moat_and_durability,
            ),
            financial_profile=FinancialProfile(
                key_metrics_updated=KeyMetrics(
                    trailing_pe=report.updated_trailing_pe,
                    ev_ebit=report.updated_ev_ebit,
                    price_to_book=report.updated_price_to_book,
                    revenue_growth_3y_cagr_pct=report.updated_revenue_growth_3y_cagr_pct,
                    free_cash_flow_yield_pct=report.updated_free_cash_flow_yield_pct,
                    net_debt_to_ebitda=report.updated_net_debt_to_ebitda,
                    piotroski_f_score=report.updated_piotroski_f_score,
                    altman_z_score=report.updated_altman_z_score,
                    insider_buying_last_6m=report.updated_insider_buying_last_6m,
                ),
                revenue_and_growth_quality=report.revenue_and_growth_quality,
                profitability_and_margin_structure=report.profitability_and_margin_structure,
                balance_sheet_and_liquidity=report.balance_sheet_and_liquidity,
                cash_flow_and_capital_intensity=report.cash_flow_and_capital_intensity,
                capital_allocation=report.capital_allocation,
            ),
            management_assessment=ManagementAssessment(
                leadership_and_execution=report.leadership_and_execution,
                governance_and_alignment=report.governance_and_alignment,
                communication_quality=report.communication_quality,
                key_concerns=report.key_concerns,
            ),
            market_narrative=MarketNarrative(
                dominant_narrative=report.dominant_narrative,
                bull_case_in_market=report.bull_case_in_market,
                bear_case_in_market=report.bear_case_in_market,
                expectations_implied_by_price=report.expectations_implied_by_price,
                where_expectations_may_be_wrong=report.where_expectations_may_be_wrong,
                narrative_monitoring_signals=narrative_signals,
            ),
            risks=risks,
            potential_catalysts=catalysts,
            data_gaps_update=DataGapsUpdate(
                original_data_gaps=report.original_data_gaps,
                closed_gaps=closed_gaps,
                remaining_open_gaps=remaining_open_gaps,
                material_open_gaps=material_open_gaps,
            ),
            source_notes=source_notes,
        )
        return payload.model_dump_json()

    if execution.agent_name == AgentNameDb.STRATEGIST:
        row = session.exec(
            select(MispricingThesis).where(
                MispricingThesis.agent_execution_id == execution.id
            )
        ).first()
        run = session.get(Run, execution.run_id)
        if row is None or run is None:
            return "{}"
        conditions = [
            r.condition_text
            for r in session.exec(
                select(MispricingThesisFalsificationCondition)
                .where(
                    MispricingThesisFalsificationCondition.mispricing_thesis_id
                    == row.id
                )
                .order_by(MispricingThesisFalsificationCondition.sort_order)
            )
        ]
        risks = [
            r.risk_text
            for r in session.exec(
                select(MispricingThesisRisk)
                .where(MispricingThesisRisk.mispricing_thesis_id == row.id)
                .order_by(MispricingThesisRisk.sort_order)
            )
        ]
        questions = [
            r.question_text
            for r in session.exec(
                select(MispricingThesisEvaluationQuestion)
                .where(
                    MispricingThesisEvaluationQuestion.mispricing_thesis_id == row.id
                )
                .order_by(MispricingThesisEvaluationQuestion.sort_order)
            )
        ]
        scenarios = [
            r.scenario_text
            for r in session.exec(
                select(MispricingThesisPermanentLossScenario)
                .where(
                    MispricingThesisPermanentLossScenario.mispricing_thesis_id == row.id
                )
                .order_by(MispricingThesisPermanentLossScenario.sort_order)
            )
        ]
        payload = MispricingThesisSchema(
            ticker=run.ticker,
            company_name=run.company_name,
            mispricing_type=row.mispricing_type,
            market_belief=row.market_belief,
            mispricing_argument=row.mispricing_argument,
            resolution_mechanism=row.resolution_mechanism,
            falsification_conditions=conditions,
            thesis_risks=risks,
            evaluation_questions=questions,
            permanent_loss_scenarios=scenarios,
            conviction_level=row.conviction_level,
        )
        return payload.model_dump_json()

    if execution.agent_name == AgentNameDb.SENTINEL:
        row = session.exec(
            select(EvaluationReport).where(
                EvaluationReport.agent_execution_id == execution.id
            )
        ).first()
        run = session.get(Run, execution.run_id)
        if row is None or run is None:
            return "{}"
        qas = [
            QuestionAssessment(
                question=r.question,
                evidence=r.evidence,
                verdict=r.verdict,
                confidence=r.confidence,
            )
            for r in session.exec(
                select(EvaluationQuestionAssessment)
                .where(EvaluationQuestionAssessment.evaluation_report_id == row.id)
                .order_by(EvaluationQuestionAssessment.sort_order)
            )
        ]
        caveats = [
            c.caveat
            for c in session.exec(
                select(EvaluationCaveat)
                .where(EvaluationCaveat.evaluation_report_id == row.id)
                .order_by(EvaluationCaveat.sort_order)
            )
        ]
        payload = EvaluationReportSchema(
            ticker=run.ticker,
            company_name=run.company_name,
            question_assessments=qas,
            red_flag_screen=RedFlagScreen(
                governance_concerns=row.governance_concerns,
                balance_sheet_stress=row.balance_sheet_stress,
                customer_or_supplier_concentration=row.customer_or_supplier_concentration,
                accounting_quality=row.accounting_quality,
                related_party_transactions=row.related_party_transactions,
                litigation_or_regulatory_risk=row.litigation_or_regulatory_risk,
                overall_red_flag_verdict=OverallRedFlagVerdict(
                    row.overall_red_flag_verdict
                ),
            ),
            thesis_verdict=ThesisVerdict(row.thesis_verdict),
            verdict_rationale=row.verdict_rationale,
            material_data_gaps=row.material_data_gaps,
            caveats=caveats,
        )
        return payload.model_dump_json()

    if execution.agent_name == AgentNameDb.APPRAISER:
        row = session.exec(
            select(AppraiserReport).where(
                AppraiserReport.agent_execution_id == execution.id
            )
        ).first()
        run = session.get(Run, execution.run_id)
        if row is None or run is None:
            return "{}"
        payload = AppraiserOutput(
            stock_data=StockData(
                ticker=run.ticker,
                name=run.company_name,
                ebit=row.ebit,
                revenue=row.revenue,
                capital_expenditure=row.capital_expenditure,
                n_shares_outstanding=row.n_shares_outstanding,
                market_cap=row.market_cap,
                gross_debt=row.gross_debt,
                gross_debt_last_year=row.gross_debt_last_year,
                net_debt=row.net_debt,
                total_interest_expense=row.total_interest_expense,
                beta=row.beta,
            ),
            stock_assumptions=StockAssumptions(
                reasoning=row.reasoning,
                forecast_period_years=row.forecast_period_years,
                assumed_tax_rate=row.assumed_tax_rate,
                assumed_forecast_period_annual_revenue_growth_rate=row.assumed_forecast_period_annual_revenue_growth_rate,
                assumed_perpetuity_cash_flow_growth_rate=row.assumed_perpetuity_cash_flow_growth_rate,
                assumed_ebit_margin=row.assumed_ebit_margin,
                assumed_depreciation_and_amortization_rate=row.assumed_depreciation_and_amortization_rate,
                assumed_capex_rate=row.assumed_capex_rate,
                assumed_change_in_working_capital_rate=row.assumed_change_in_working_capital_rate,
            ),
        )
        return payload.model_dump_json()

    if execution.agent_name == AgentNameDb.ARBITER:
        run_final = session.exec(
            select(RunFinalDecision).where(
                RunFinalDecision.run_id == execution.run_id,
                RunFinalDecision.decision_type == DecisionTypeDb.ARBITER,
            )
        ).first()
        run = session.get(Run, execution.run_id)
        if run_final is None or run is None:
            return "{}"
        supporting = [
            r.factor_text
            for r in session.exec(
                select(RunFinalDecisionSupportingFactor)
                .where(
                    RunFinalDecisionSupportingFactor.run_final_decision_id
                    == run_final.id
                )
                .order_by(RunFinalDecisionSupportingFactor.sort_order)
            )
        ]
        mitigating = [
            r.factor_text
            for r in session.exec(
                select(RunFinalDecisionMitigatingFactor)
                .where(
                    RunFinalDecisionMitigatingFactor.run_final_decision_id
                    == run_final.id
                )
                .order_by(RunFinalDecisionMitigatingFactor.sort_order)
            )
        ]
        payload = ArbiterDecision(
            ticker=run.ticker,
            company_name=run.company_name,
            decision_date=run_final.decision_date.isoformat(),
            is_existing_position=run_final.is_existing_position,
            rating=run_final.rating,
            recommended_action=run_final.recommended_action,
            conviction=run_final.conviction or "Medium",
            margin_of_safety=MarginOfSafetyAssessment(
                current_price=run_final.current_price or 0.0,
                bear_intrinsic_value=run_final.bear_intrinsic_value or 0.0,
                base_intrinsic_value=run_final.base_intrinsic_value or 0.0,
                bull_intrinsic_value=run_final.bull_intrinsic_value or 0.0,
                margin_of_safety_base_pct=run_final.margin_of_safety_base_pct or 0.0,
                margin_of_safety_verdict=run_final.margin_of_safety_verdict or "",
            ),
            rationale=ArbiterRationale(
                primary_driver=run_final.primary_driver or "",
                supporting_factors=supporting,
                mitigating_factors=mitigating,
                red_flag_disposition=run_final.red_flag_disposition or "",
                data_gap_disposition=run_final.data_gap_disposition or "",
            ),
            thesis_expiry_note=run_final.thesis_expiry_note or "",
        )
        return payload.model_dump_json()

    return "{}"


def get_conversation_for_workflow_surveyor(
    session: Session,
    workflow_run_id: str,
) -> dict[str, str] | None:
    execution = session.exec(
        select(WorkflowAgentExecution).where(
            WorkflowAgentExecution.workflow_run_id == workflow_run_id,
            WorkflowAgentExecution.agent_name == AgentNameDb.SURVEYOR,
        )
    ).first()
    if execution is None:
        return None
    conversation = session.exec(
        select(AgentConversation).where(
            AgentConversation.workflow_agent_execution_id == execution.id
        )
    ).first()
    if conversation is None:
        return None
    return {
        "system_prompt": conversation.system_prompt,
        "messages_json": _build_messages_json(session, conversation.id),
        "assistant_response": _assistant_response_for_workflow_execution(
            session, execution
        ),
    }


def get_conversation_for_run_agent(
    session: Session,
    *,
    run_id: str,
    agent_name: str,
) -> dict[str, str] | None:
    execution = session.exec(
        select(AgentExecution).where(
            AgentExecution.run_id == run_id,
            AgentExecution.agent_name == AgentNameDb(agent_name),
        )
    ).first()
    if execution is None:
        return None
    conversation = session.exec(
        select(AgentConversation).where(
            AgentConversation.agent_execution_id == execution.id
        )
    ).first()
    if conversation is None:
        return None
    return {
        "system_prompt": conversation.system_prompt,
        "messages_json": _build_messages_json(session, conversation.id),
        "assistant_response": _assistant_response_for_run_agent(session, execution),
    }


def delete_workflow_run_if_mock(session: Session, workflow_run_id: str) -> bool:
    wf = session.get(WorkflowRun, workflow_run_id)
    if wf is None or not wf.is_mock:
        return False
    session.delete(wf)
    session.commit()
    return True


def workflow_run_exists(session: Session, workflow_run_id: str) -> bool:
    return session.get(WorkflowRun, workflow_run_id) is not None


def get_latest_portfolio_tickers(session: Session) -> list[str] | None:
    workflow = session.exec(
        select(WorkflowRun).order_by(WorkflowRun.started_at.desc())
    ).first()
    if workflow is None:
        return None
    rows = list(
        session.exec(
            select(WorkflowRunPortfolioTicker)
            .where(WorkflowRunPortfolioTicker.workflow_run_id == workflow.id)
            .order_by(WorkflowRunPortfolioTicker.sort_order)
        )
    )
    return [r.ticker for r in rows]


def set_workflow_error(session: Session, workflow_run_id: str, message: str) -> None:
    wf = session.get(WorkflowRun, workflow_run_id)
    if wf is None:
        return
    wf.status = WorkflowRunStatusDb.FAILED
    wf.error_message = message
    wf.completed_at = utc_now()
    session.add(wf)
    session.commit()
