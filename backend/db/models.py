"""SQLModel table definitions for the dashboard backend."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, Column, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel  # pyright: ignore[reportUnknownVariableType]


def _str_enum_sql_values(enum_cls: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_cls.__members__.values()]


class WorkflowRunStatusDb(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStatusDb(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EntryPathDb(StrEnum):
    SURVEYOR = "surveyor"
    PROFILER = "profiler"


class AgentNameDb(StrEnum):
    SURVEYOR = "surveyor"
    PROFILER = "profiler"
    RESEARCHER = "researcher"
    STRATEGIST = "strategist"
    SENTINEL = "sentinel"
    APPRAISER = "appraiser"
    ARBITER = "arbiter"


class DecisionTypeDb(StrEnum):
    ARBITER = "arbiter"
    SENTINEL_REJECTION = "sentinel_rejection"


class MessageKindDb(StrEnum):
    REQUEST = "request"
    RESPONSE = "response"


class MessagePartKindDb(StrEnum):
    SYSTEM_PROMPT = "system_prompt"
    USER_PROMPT = "user_prompt"
    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RETURN = "tool_return"
    RETRY_PROMPT = "retry_prompt"
    UNKNOWN = "unknown"


class WorkflowRun(SQLModel, table=True):
    __tablename__ = "workflow_runs"  # pyright: ignore[reportAssignmentType]

    id: str = Field(primary_key=True)
    started_at: datetime
    completed_at: datetime | None = None
    status: WorkflowRunStatusDb = Field(default=WorkflowRunStatusDb.RUNNING)
    is_mock: bool
    error_message: str | None = None


class WorkflowRunPortfolioTicker(SQLModel, table=True):
    __tablename__ = "workflow_run_portfolio_tickers"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("workflow_run_id", "sort_order"),)

    id: str = Field(primary_key=True)
    workflow_run_id: str = Field(foreign_key="workflow_runs.id", index=True)
    sort_order: int
    ticker: str


class WorkflowAgentExecution(SQLModel, table=True):
    __tablename__ = "workflow_agent_executions"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("workflow_run_id", "agent_name"),)

    id: str = Field(primary_key=True)
    workflow_run_id: str = Field(foreign_key="workflow_runs.id", index=True)
    agent_name: AgentNameDb
    status: ExecutionStatusDb = Field(default=ExecutionStatusDb.PENDING)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


class Run(SQLModel, table=True):
    __tablename__ = "runs"  # pyright: ignore[reportAssignmentType]

    id: str = Field(primary_key=True)
    workflow_run_id: str = Field(foreign_key="workflow_runs.id", index=True)
    candidate_snapshot_id: str | None = Field(
        default=None,
        foreign_key="candidate_snapshots.id",
        index=True,
    )
    ticker: str
    company_name: str
    started_at: datetime
    completed_at: datetime | None = None
    entry_path: EntryPathDb
    is_existing_position: bool
    status: WorkflowRunStatusDb = Field(default=WorkflowRunStatusDb.RUNNING)
    is_mock: bool
    error_message: str | None = None
    final_rating: str | None = None
    decision_type: DecisionTypeDb | None = None
    recommended_action: str | None = None


class AgentExecution(SQLModel, table=True):
    __tablename__ = "agent_executions"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("run_id", "agent_name"),)

    id: str = Field(primary_key=True)
    run_id: str = Field(foreign_key="runs.id", index=True)
    agent_name: AgentNameDb
    status: ExecutionStatusDb = Field(default=ExecutionStatusDb.PENDING)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


class CandidateSnapshot(SQLModel, table=True):
    __tablename__ = "candidate_snapshots"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        CheckConstraint(
            "(workflow_agent_execution_id IS NOT NULL) <> (agent_execution_id IS NOT NULL)"
        ),
        UniqueConstraint("workflow_agent_execution_id", "sort_order"),
        UniqueConstraint("agent_execution_id"),
    )

    id: str = Field(primary_key=True)
    workflow_agent_execution_id: str | None = Field(
        default=None,
        foreign_key="workflow_agent_executions.id",
        index=True,
    )
    agent_execution_id: str | None = Field(
        default=None,
        foreign_key="agent_executions.id",
        index=True,
    )
    sort_order: int
    ticker: str
    company_name: str
    exchange: str
    currency: str
    market_cap_local: int
    market_cap_display: str
    sector: str
    industry: str
    analyst_coverage_count: int | None = None
    trailing_pe: float | None = None
    ev_ebit: float | None = None
    price_to_book: float | None = None
    revenue_growth_3y_cagr_pct: float | None = None
    free_cash_flow_yield_pct: float | None = None
    net_debt_to_ebitda: float | None = None
    piotroski_f_score: int | None = None
    altman_z_score: float | None = None
    insider_buying_last_6m: bool | None = None
    rationale: str
    red_flags: str
    data_gaps: str


class ResearchReport(SQLModel, table=True):
    __tablename__ = "research_reports"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("agent_execution_id"),)

    id: str = Field(primary_key=True)
    agent_execution_id: str = Field(foreign_key="agent_executions.id", index=True)
    candidate_snapshot_id: str = Field(foreign_key="candidate_snapshots.id", index=True)
    executive_overview: str
    products_and_services: str
    customer_segments: str
    unit_economics: str
    competitive_positioning: str
    moat_and_durability: str
    updated_trailing_pe: float | None = None
    updated_ev_ebit: float | None = None
    updated_price_to_book: float | None = None
    updated_revenue_growth_3y_cagr_pct: float | None = None
    updated_free_cash_flow_yield_pct: float | None = None
    updated_net_debt_to_ebitda: float | None = None
    updated_piotroski_f_score: int | None = None
    updated_altman_z_score: float | None = None
    updated_insider_buying_last_6m: bool | None = None
    revenue_and_growth_quality: str
    profitability_and_margin_structure: str
    balance_sheet_and_liquidity: str
    cash_flow_and_capital_intensity: str
    capital_allocation: str
    leadership_and_execution: str
    governance_and_alignment: str
    communication_quality: str
    key_concerns: str
    dominant_narrative: str
    bull_case_in_market: str
    bear_case_in_market: str
    expectations_implied_by_price: str
    where_expectations_may_be_wrong: str
    original_data_gaps: str


class ResearchReportNarrativeMonitoringSignal(SQLModel, table=True):
    __tablename__ = "research_report_narrative_monitoring_signals"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("research_report_id", "sort_order"),)

    id: str = Field(primary_key=True)
    research_report_id: str = Field(foreign_key="research_reports.id", index=True)
    sort_order: int
    signal: str


class ResearchReportRisk(SQLModel, table=True):
    __tablename__ = "research_report_risks"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("research_report_id", "sort_order"),)

    id: str = Field(primary_key=True)
    research_report_id: str = Field(foreign_key="research_reports.id", index=True)
    sort_order: int
    risk: str


class ResearchReportPotentialCatalyst(SQLModel, table=True):
    __tablename__ = "research_report_potential_catalysts"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("research_report_id", "sort_order"),)

    id: str = Field(primary_key=True)
    research_report_id: str = Field(foreign_key="research_reports.id", index=True)
    sort_order: int
    catalyst: str


class ResearchReportClosedGap(SQLModel, table=True):
    __tablename__ = "research_report_closed_gaps"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("research_report_id", "sort_order"),)

    id: str = Field(primary_key=True)
    research_report_id: str = Field(foreign_key="research_reports.id", index=True)
    sort_order: int
    gap_text: str


class ResearchReportRemainingOpenGap(SQLModel, table=True):
    __tablename__ = "research_report_remaining_open_gaps"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("research_report_id", "sort_order"),)

    id: str = Field(primary_key=True)
    research_report_id: str = Field(foreign_key="research_reports.id", index=True)
    sort_order: int
    gap_text: str


class ResearchReportMaterialOpenGap(SQLModel, table=True):
    __tablename__ = "research_report_material_open_gaps"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("research_report_id", "sort_order"),)

    id: str = Field(primary_key=True)
    research_report_id: str = Field(foreign_key="research_reports.id", index=True)
    sort_order: int
    gap_text: str


class ResearchReportSourceNote(SQLModel, table=True):
    __tablename__ = "research_report_source_notes"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("research_report_id", "sort_order"),)

    id: str = Field(primary_key=True)
    research_report_id: str = Field(foreign_key="research_reports.id", index=True)
    sort_order: int
    source_note: str


class MispricingThesis(SQLModel, table=True):
    __tablename__ = "mispricing_theses"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("agent_execution_id"),)

    id: str = Field(primary_key=True)
    agent_execution_id: str = Field(foreign_key="agent_executions.id", index=True)
    mispricing_type: str
    market_belief: str
    mispricing_argument: str
    resolution_mechanism: str
    conviction_level: str


class MispricingThesisFalsificationCondition(SQLModel, table=True):
    __tablename__ = "mispricing_thesis_falsification_conditions"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("mispricing_thesis_id", "sort_order"),)

    id: str = Field(primary_key=True)
    mispricing_thesis_id: str = Field(foreign_key="mispricing_theses.id", index=True)
    sort_order: int
    condition_text: str


class MispricingThesisRisk(SQLModel, table=True):
    __tablename__ = "mispricing_thesis_risks"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("mispricing_thesis_id", "sort_order"),)

    id: str = Field(primary_key=True)
    mispricing_thesis_id: str = Field(foreign_key="mispricing_theses.id", index=True)
    sort_order: int
    risk_text: str


class MispricingThesisEvaluationQuestion(SQLModel, table=True):
    __tablename__ = "mispricing_thesis_evaluation_questions"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("mispricing_thesis_id", "sort_order"),)

    id: str = Field(primary_key=True)
    mispricing_thesis_id: str = Field(foreign_key="mispricing_theses.id", index=True)
    sort_order: int
    question_text: str


class MispricingThesisPermanentLossScenario(SQLModel, table=True):
    __tablename__ = "mispricing_thesis_permanent_loss_scenarios"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("mispricing_thesis_id", "sort_order"),)

    id: str = Field(primary_key=True)
    mispricing_thesis_id: str = Field(foreign_key="mispricing_theses.id", index=True)
    sort_order: int
    scenario_text: str


class EvaluationReport(SQLModel, table=True):
    __tablename__ = "evaluation_reports"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("agent_execution_id"),)

    id: str = Field(primary_key=True)
    agent_execution_id: str = Field(foreign_key="agent_executions.id", index=True)
    governance_concerns: str
    balance_sheet_stress: str
    customer_or_supplier_concentration: str
    accounting_quality: str
    related_party_transactions: str
    litigation_or_regulatory_risk: str
    overall_red_flag_verdict: str
    thesis_verdict: str
    verdict_rationale: str
    material_data_gaps: str


class EvaluationQuestionAssessment(SQLModel, table=True):
    __tablename__ = "evaluation_question_assessments"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("evaluation_report_id", "sort_order"),)

    id: str = Field(primary_key=True)
    evaluation_report_id: str = Field(foreign_key="evaluation_reports.id", index=True)
    sort_order: int
    question: str
    evidence: str
    verdict: str
    confidence: str


class EvaluationCaveat(SQLModel, table=True):
    __tablename__ = "evaluation_caveats"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("evaluation_report_id", "sort_order"),)

    id: str = Field(primary_key=True)
    evaluation_report_id: str = Field(foreign_key="evaluation_reports.id", index=True)
    sort_order: int
    caveat: str


class AppraiserReport(SQLModel, table=True):
    __tablename__ = "appraiser_reports"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("agent_execution_id"),)

    id: str = Field(primary_key=True)
    agent_execution_id: str = Field(foreign_key="agent_executions.id", index=True)
    ebit: float
    revenue: float
    capital_expenditure: float
    n_shares_outstanding: float
    market_cap: float
    gross_debt: float
    gross_debt_last_year: float
    net_debt: float
    total_interest_expense: float
    beta: float
    reasoning: str
    forecast_period_years: int
    assumed_tax_rate: float
    assumed_forecast_period_annual_revenue_growth_rate: float
    assumed_perpetuity_cash_flow_growth_rate: float
    assumed_ebit_margin: float
    assumed_depreciation_and_amortization_rate: float
    assumed_capex_rate: float
    assumed_change_in_working_capital_rate: float


class DcfValuation(SQLModel, table=True):
    __tablename__ = "dcf_valuations"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        UniqueConstraint("run_id"),
        UniqueConstraint("appraiser_agent_execution_id"),
    )

    id: str = Field(primary_key=True)
    run_id: str = Field(foreign_key="runs.id", index=True)
    appraiser_agent_execution_id: str = Field(
        foreign_key="agent_executions.id",
        index=True,
    )
    intrinsic_share_price: float
    enterprise_value: float
    equity_value: float


class RunFinalDecision(SQLModel, table=True):
    __tablename__ = "run_final_decisions"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        UniqueConstraint("run_id"),
        CheckConstraint(
            """
            (
                decision_type = 'arbiter'
                AND rejection_reason IS NULL
                AND conviction IS NOT NULL
                AND current_price IS NOT NULL
                AND bear_intrinsic_value IS NOT NULL
                AND base_intrinsic_value IS NOT NULL
                AND bull_intrinsic_value IS NOT NULL
                AND margin_of_safety_base_pct IS NOT NULL
                AND margin_of_safety_verdict IS NOT NULL
                AND primary_driver IS NOT NULL
                AND red_flag_disposition IS NOT NULL
                AND data_gap_disposition IS NOT NULL
                AND thesis_expiry_note IS NOT NULL
            )
            OR
            (
                decision_type = 'sentinel_rejection'
                AND rejection_reason IS NOT NULL
                AND conviction IS NULL
                AND current_price IS NULL
                AND bear_intrinsic_value IS NULL
                AND base_intrinsic_value IS NULL
                AND bull_intrinsic_value IS NULL
                AND margin_of_safety_base_pct IS NULL
                AND margin_of_safety_verdict IS NULL
                AND primary_driver IS NULL
                AND red_flag_disposition IS NULL
                AND data_gap_disposition IS NULL
                AND thesis_expiry_note IS NULL
            )
            """
        ),
    )

    id: str = Field(primary_key=True)
    run_id: str = Field(foreign_key="runs.id", index=True)
    source_agent_execution_id: str = Field(
        foreign_key="agent_executions.id", index=True
    )
    decision_type: DecisionTypeDb = Field(
        sa_column=Column(
            SAEnum(
                DecisionTypeDb,
                native_enum=False,
                values_callable=_str_enum_sql_values,
            ),
            nullable=False,
        ),
    )
    decision_date: date
    is_existing_position: bool
    rating: str
    recommended_action: str
    conviction: str | None = None
    rejection_reason: str | None = None
    current_price: float | None = None
    bear_intrinsic_value: float | None = None
    base_intrinsic_value: float | None = None
    bull_intrinsic_value: float | None = None
    margin_of_safety_base_pct: float | None = None
    margin_of_safety_verdict: str | None = None
    primary_driver: str | None = None
    red_flag_disposition: str | None = None
    data_gap_disposition: str | None = None
    thesis_expiry_note: str | None = None


class RunFinalDecisionSupportingFactor(SQLModel, table=True):
    __tablename__ = "run_final_decision_supporting_factors"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("run_final_decision_id", "sort_order"),)

    id: str = Field(primary_key=True)
    run_final_decision_id: str = Field(foreign_key="run_final_decisions.id", index=True)
    sort_order: int
    factor_text: str


class RunFinalDecisionMitigatingFactor(SQLModel, table=True):
    __tablename__ = "run_final_decision_mitigating_factors"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("run_final_decision_id", "sort_order"),)

    id: str = Field(primary_key=True)
    run_final_decision_id: str = Field(foreign_key="run_final_decisions.id", index=True)
    sort_order: int
    factor_text: str


class AgentConversation(SQLModel, table=True):
    __tablename__ = "agent_conversations"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        CheckConstraint(
            "(workflow_agent_execution_id IS NOT NULL) <> (agent_execution_id IS NOT NULL)"
        ),
        UniqueConstraint("workflow_agent_execution_id"),
        UniqueConstraint("agent_execution_id"),
    )

    id: str = Field(primary_key=True)
    workflow_agent_execution_id: str | None = Field(
        default=None,
        foreign_key="workflow_agent_executions.id",
        index=True,
    )
    agent_execution_id: str | None = Field(
        default=None,
        foreign_key="agent_executions.id",
        index=True,
    )
    system_prompt: str


class AgentConversationMessage(SQLModel, table=True):
    __tablename__ = "agent_conversation_messages"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (UniqueConstraint("conversation_id", "message_index"),)

    id: str = Field(primary_key=True)
    conversation_id: str = Field(foreign_key="agent_conversations.id", index=True)
    message_index: int
    message_kind: MessageKindDb = Field(
        sa_column=Column(
            SAEnum(
                MessageKindDb,
                native_enum=False,
                values_callable=_str_enum_sql_values,
            ),
            nullable=False,
        ),
    )


class AgentConversationMessagePart(SQLModel, table=True):
    __tablename__ = "agent_conversation_message_parts"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        UniqueConstraint("conversation_message_id", "part_index"),
        CheckConstraint(
            """
            (
                part_kind IN ('system_prompt', 'user_prompt', 'text', 'retry_prompt', 'unknown')
                AND content_text IS NOT NULL
            )
            OR
            (
                part_kind = 'tool_call'
                AND tool_name IS NOT NULL
                AND tool_call_id IS NOT NULL
            )
            OR
            (
                part_kind = 'tool_return'
                AND content_text IS NOT NULL
                AND tool_name IS NOT NULL
                AND tool_call_id IS NOT NULL
            )
            """
        ),
    )

    id: str = Field(primary_key=True)
    conversation_message_id: str = Field(
        foreign_key="agent_conversation_messages.id",
        index=True,
    )
    part_index: int
    part_kind: MessagePartKindDb = Field(
        sa_column=Column(
            SAEnum(
                MessagePartKindDb,
                native_enum=False,
                values_callable=_str_enum_sql_values,
            ),
            nullable=False,
        ),
    )
    content_text: str | None = None
    tool_name: str | None = None
    tool_call_id: str | None = None
