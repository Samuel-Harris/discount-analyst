"""Agent conversation persistence and serialised assistant payloads."""

from __future__ import annotations

import json
from typing import Any, Literal, cast

from pydantic_ai import ModelMessagesTypeAdapter
from pydantic_ai.messages import ModelMessage
from sqlmodel import Session, col, delete, select

from backend.crud.candidate_snapshots import snapshot_to_candidate
from backend.crud.db_utils import dump_json_string, new_id
from backend.db.models import (
    AgentConversation,
    AgentConversationMessage,
    AgentConversationMessagePart,
    AgentExecution,
    AgentNameDb,
    AppraiserReport,
    CandidateSnapshot,
    DecisionTypeDb,
    EvaluationCaveat,
    EvaluationQuestionAssessment,
    EvaluationReport,
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
)
from discount_analyst.agents.appraiser.schema import AppraiserOutput
from discount_analyst.agents.arbiter.schema import (
    ArbiterDecision,
    ArbiterRationale,
    MarginOfSafetyAssessment,
    MarginOfSafetyVerdict,
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
from discount_analyst.agents.surveyor.schema import KeyMetrics, SurveyorOutput
from discount_analyst.rating import InvestmentRating
from discount_analyst.valuation.schema import StockAssumptions, StockData


def _optional_json_str(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def message_part_kind_from_raw(raw: str) -> MessagePartKindDb:
    mapping = {
        "system-prompt": MessagePartKindDb.SYSTEM_PROMPT,
        "user-prompt": MessagePartKindDb.USER_PROMPT,
        "text": MessagePartKindDb.TEXT,
        "tool-call": MessagePartKindDb.TOOL_CALL,
        "tool-return": MessagePartKindDb.TOOL_RETURN,
        "retry-prompt": MessagePartKindDb.RETRY_PROMPT,
    }
    return mapping[raw]


def message_part_kind_to_raw(kind: MessagePartKindDb) -> str:
    mapping = {
        MessagePartKindDb.SYSTEM_PROMPT: "system-prompt",
        MessagePartKindDb.USER_PROMPT: "user-prompt",
        MessagePartKindDb.TEXT: "text",
        MessagePartKindDb.TOOL_CALL: "tool-call",
        MessagePartKindDb.TOOL_RETURN: "tool-return",
        MessagePartKindDb.RETRY_PROMPT: "retry-prompt",
    }
    return mapping[kind]


def parse_messages_payload(
    *,
    messages: list[object] | None,
    messages_json: str | None,
) -> list[dict[str, Any]]:
    if messages is not None:
        return ModelMessagesTypeAdapter.dump_python(
            cast(list[ModelMessage], messages), mode="json"
        )
    if messages_json:
        loaded = json.loads(messages_json)
        if isinstance(loaded, list):
            return cast(list[dict[str, Any]], loaded)
    return []


def replace_conversation_messages(
    session: Session,
    *,
    conversation_id: str,
    messages_payload: list[dict[str, Any]],
) -> None:
    existing_messages = list(
        session.scalars(
            select(AgentConversationMessage).where(
                col(AgentConversationMessage.conversation_id) == conversation_id
            )
        )
    )
    for msg in existing_messages:
        session.exec(
            delete(AgentConversationMessagePart).where(
                col(AgentConversationMessagePart.conversation_message_id) == msg.id
            )
        )
    session.exec(
        delete(AgentConversationMessage).where(
            col(AgentConversationMessage.conversation_id) == conversation_id
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
        parts_any: Any = message_obj.get("parts", [])
        if not isinstance(parts_any, list):
            continue
        parts_list = cast(list[Any], parts_any)
        for part_index, part_obj in enumerate(parts_list):
            if not isinstance(part_obj, dict):
                continue
            part_dict = cast(dict[str, Any], part_obj)
            raw_kind = str(part_dict.get("part_kind", "text"))
            kind = message_part_kind_from_raw(raw_kind)
            content_text: str | None = None
            if kind == MessagePartKindDb.TOOL_CALL:
                content_text = dump_json_string(part_dict.get("args", ""))
            elif "content" in part_dict:
                content_text = dump_json_string(part_dict.get("content"))

            part_row = AgentConversationMessagePart(
                id=new_id(),
                conversation_message_id=msg_row.id,
                part_index=part_index,
                part_kind=kind,
                content_text=content_text,
                tool_name=_optional_json_str(part_dict.get("tool_name")),
                tool_call_id=_optional_json_str(part_dict.get("tool_call_id")),
            )
            session.add(part_row)


def build_messages_json(session: Session, conversation_id: str) -> str:
    msg_rows = list(
        session.scalars(
            select(AgentConversationMessage)
            .where(col(AgentConversationMessage.conversation_id) == conversation_id)
            .order_by(col(AgentConversationMessage.message_index))
        )
    )
    out: list[dict[str, Any]] = []
    for msg_row in msg_rows:
        parts_rows = list(
            session.scalars(
                select(AgentConversationMessagePart)
                .where(
                    col(AgentConversationMessagePart.conversation_message_id)
                    == msg_row.id
                )
                .order_by(col(AgentConversationMessagePart.part_index))
            )
        )
        parts: list[dict[str, Any]] = []
        for part_row in parts_rows:
            raw_kind = message_part_kind_to_raw(part_row.part_kind)
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
    existing = session.scalars(
        select(AgentConversation).where(
            col(AgentConversation.workflow_agent_execution_id)
            == workflow_agent_execution_id
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
    payload = parse_messages_payload(messages=messages, messages_json=messages_json)
    replace_conversation_messages(
        session, conversation_id=conversation_id, messages_payload=payload
    )


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
    existing = session.scalars(
        select(AgentConversation).where(
            col(AgentConversation.agent_execution_id) == agent_execution_id
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
    payload = parse_messages_payload(messages=messages, messages_json=messages_json)
    replace_conversation_messages(
        session, conversation_id=conversation_id, messages_payload=payload
    )


def assistant_response_for_workflow_execution(
    session: Session, execution: WorkflowAgentExecution
) -> str:
    snapshots = list(
        session.scalars(
            select(CandidateSnapshot)
            .where(col(CandidateSnapshot.workflow_agent_execution_id) == execution.id)
            .order_by(col(CandidateSnapshot.sort_order))
        )
    )
    output = SurveyorOutput.model_construct(
        candidates=[snapshot_to_candidate(s) for s in snapshots]
    )
    return output.model_dump_json()


def assistant_response_for_run_agent(
    session: Session, execution: AgentExecution
) -> str:
    if execution.agent_name == AgentNameDb.PROFILER:
        snapshot = session.scalars(
            select(CandidateSnapshot).where(
                col(CandidateSnapshot.agent_execution_id) == execution.id
            )
        ).first()
        if snapshot is None:
            return "{}"
        return ProfilerOutput(
            candidate=snapshot_to_candidate(snapshot)
        ).model_dump_json()

    if execution.agent_name == AgentNameDb.RESEARCHER:
        report = session.scalars(
            select(ResearchReport).where(
                col(ResearchReport.agent_execution_id) == execution.id
            )
        ).first()
        if report is None:
            return "{}"
        snapshot = session.get(CandidateSnapshot, report.candidate_snapshot_id)
        if snapshot is None:
            return "{}"
        narrative_signals = [
            r.signal
            for r in session.scalars(
                select(ResearchReportNarrativeMonitoringSignal)
                .where(
                    col(ResearchReportNarrativeMonitoringSignal.research_report_id)
                    == report.id
                )
                .order_by(col(ResearchReportNarrativeMonitoringSignal.sort_order))
            )
        ]
        risks = [
            r.risk
            for r in session.scalars(
                select(ResearchReportRisk)
                .where(col(ResearchReportRisk.research_report_id) == report.id)
                .order_by(col(ResearchReportRisk.sort_order))
            )
        ]
        catalysts = [
            r.catalyst
            for r in session.scalars(
                select(ResearchReportPotentialCatalyst)
                .where(
                    col(ResearchReportPotentialCatalyst.research_report_id) == report.id
                )
                .order_by(col(ResearchReportPotentialCatalyst.sort_order))
            )
        ]
        closed_gaps = [
            r.gap_text
            for r in session.scalars(
                select(ResearchReportClosedGap)
                .where(col(ResearchReportClosedGap.research_report_id) == report.id)
                .order_by(col(ResearchReportClosedGap.sort_order))
            )
        ]
        remaining_open_gaps = [
            r.gap_text
            for r in session.scalars(
                select(ResearchReportRemainingOpenGap)
                .where(
                    col(ResearchReportRemainingOpenGap.research_report_id) == report.id
                )
                .order_by(col(ResearchReportRemainingOpenGap.sort_order))
            )
        ]
        material_open_gaps = [
            r.gap_text
            for r in session.scalars(
                select(ResearchReportMaterialOpenGap)
                .where(
                    col(ResearchReportMaterialOpenGap.research_report_id) == report.id
                )
                .order_by(col(ResearchReportMaterialOpenGap.sort_order))
            )
        ]
        source_notes = [
            r.source_note
            for r in session.scalars(
                select(ResearchReportSourceNote)
                .where(col(ResearchReportSourceNote.research_report_id) == report.id)
                .order_by(col(ResearchReportSourceNote.sort_order))
            )
        ]
        payload = DeepResearchReport(
            candidate=snapshot_to_candidate(snapshot),
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
        row = session.scalars(
            select(MispricingThesis).where(
                col(MispricingThesis.agent_execution_id) == execution.id
            )
        ).first()
        run = session.get(Run, execution.run_id)
        if row is None or run is None:
            return "{}"
        conditions = [
            r.condition_text
            for r in session.scalars(
                select(MispricingThesisFalsificationCondition)
                .where(
                    col(MispricingThesisFalsificationCondition.mispricing_thesis_id)
                    == row.id
                )
                .order_by(col(MispricingThesisFalsificationCondition.sort_order))
            )
        ]
        risks = [
            r.risk_text
            for r in session.scalars(
                select(MispricingThesisRisk)
                .where(col(MispricingThesisRisk.mispricing_thesis_id) == row.id)
                .order_by(col(MispricingThesisRisk.sort_order))
            )
        ]
        questions = [
            r.question_text
            for r in session.scalars(
                select(MispricingThesisEvaluationQuestion)
                .where(
                    col(MispricingThesisEvaluationQuestion.mispricing_thesis_id)
                    == row.id
                )
                .order_by(col(MispricingThesisEvaluationQuestion.sort_order))
            )
        ]
        scenarios = [
            r.scenario_text
            for r in session.scalars(
                select(MispricingThesisPermanentLossScenario)
                .where(
                    col(MispricingThesisPermanentLossScenario.mispricing_thesis_id)
                    == row.id
                )
                .order_by(col(MispricingThesisPermanentLossScenario.sort_order))
            )
        ]
        conv_level: Literal["Low", "Medium", "High"] = cast(
            Literal["Low", "Medium", "High"], row.conviction_level
        )
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
            conviction_level=conv_level,
        )
        return payload.model_dump_json()

    if execution.agent_name == AgentNameDb.SENTINEL:
        row = session.scalars(
            select(EvaluationReport).where(
                col(EvaluationReport.agent_execution_id) == execution.id
            )
        ).first()
        run = session.get(Run, execution.run_id)
        if row is None or run is None:
            return "{}"
        qas = [
            QuestionAssessment(
                question=r.question,
                evidence=r.evidence,
                verdict=cast(
                    Literal[
                        "Supports thesis",
                        "Neutral",
                        "Weakens thesis",
                        "Breaks thesis",
                    ],
                    r.verdict,
                ),
                confidence=cast(Literal["Low", "Medium", "High"], r.confidence),
            )
            for r in session.scalars(
                select(EvaluationQuestionAssessment)
                .where(col(EvaluationQuestionAssessment.evaluation_report_id) == row.id)
                .order_by(col(EvaluationQuestionAssessment.sort_order))
            )
        ]
        caveats = [
            c.caveat
            for c in session.scalars(
                select(EvaluationCaveat)
                .where(col(EvaluationCaveat.evaluation_report_id) == row.id)
                .order_by(col(EvaluationCaveat.sort_order))
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
        row = session.scalars(
            select(AppraiserReport).where(
                col(AppraiserReport.agent_execution_id) == execution.id
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
        run_final = session.scalars(
            select(RunFinalDecision).where(
                col(RunFinalDecision.run_id) == execution.run_id,
                col(RunFinalDecision.decision_type) == DecisionTypeDb.ARBITER,
            )
        ).first()
        run = session.get(Run, execution.run_id)
        if run_final is None or run is None:
            return "{}"
        supporting = [
            r.factor_text
            for r in session.scalars(
                select(RunFinalDecisionSupportingFactor)
                .where(
                    col(RunFinalDecisionSupportingFactor.run_final_decision_id)
                    == run_final.id
                )
                .order_by(col(RunFinalDecisionSupportingFactor.sort_order))
            )
        ]
        mitigating = [
            r.factor_text
            for r in session.scalars(
                select(RunFinalDecisionMitigatingFactor)
                .where(
                    col(RunFinalDecisionMitigatingFactor.run_final_decision_id)
                    == run_final.id
                )
                .order_by(col(RunFinalDecisionMitigatingFactor.sort_order))
            )
        ]
        mos_verdict: MarginOfSafetyVerdict = cast(
            MarginOfSafetyVerdict,
            run_final.margin_of_safety_verdict
            or "None — stock appears fairly valued or overvalued",
        )
        conviction_lit: Literal["Low", "Medium", "High"] = cast(
            Literal["Low", "Medium", "High"],
            run_final.conviction or "Medium",
        )
        payload = ArbiterDecision(
            ticker=run.ticker,
            company_name=run.company_name,
            decision_date=run_final.decision_date.isoformat(),
            is_existing_position=run_final.is_existing_position,
            rating=InvestmentRating(run_final.rating),
            recommended_action=run_final.recommended_action,
            conviction=conviction_lit,
            margin_of_safety=MarginOfSafetyAssessment(
                current_price=run_final.current_price or 0.0,
                bear_intrinsic_value=run_final.bear_intrinsic_value or 0.0,
                base_intrinsic_value=run_final.base_intrinsic_value or 0.0,
                bull_intrinsic_value=run_final.bull_intrinsic_value or 0.0,
                margin_of_safety_base_pct=run_final.margin_of_safety_base_pct or 0.0,
                margin_of_safety_verdict=mos_verdict,
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
    execution = session.scalars(
        select(WorkflowAgentExecution).where(
            col(WorkflowAgentExecution.workflow_run_id) == workflow_run_id,
            col(WorkflowAgentExecution.agent_name) == AgentNameDb.SURVEYOR,
        )
    ).first()
    if execution is None:
        return None
    conversation = session.scalars(
        select(AgentConversation).where(
            col(AgentConversation.workflow_agent_execution_id) == execution.id
        )
    ).first()
    if conversation is None:
        return None
    return {
        "system_prompt": conversation.system_prompt,
        "messages_json": build_messages_json(session, conversation.id),
        "assistant_response": assistant_response_for_workflow_execution(
            session, execution
        ),
    }


def get_conversation_for_run_agent(
    session: Session,
    *,
    run_id: str,
    agent_name: str,
) -> dict[str, str] | None:
    execution = session.scalars(
        select(AgentExecution).where(
            col(AgentExecution.run_id) == run_id,
            col(AgentExecution.agent_name) == AgentNameDb(agent_name),
        )
    ).first()
    if execution is None:
        return None
    conversation = session.scalars(
        select(AgentConversation).where(
            col(AgentConversation.agent_execution_id) == execution.id
        )
    ).first()
    if conversation is None:
        return None
    return {
        "system_prompt": conversation.system_prompt,
        "messages_json": build_messages_json(session, conversation.id),
        "assistant_response": assistant_response_for_run_agent(session, execution),
    }
