"""Initial normalised dashboard schema.

This revision intentionally contains **frozen** SQLite DDL generated once from the
ORM metadata at introduction time, so later model edits do not rewrite history.

To add schema changes, create a new Alembic revision rather than editing this file.
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "0001_initial_dashboard_schema"
down_revision = None
branch_labels = None
depends_on = None

_UPGRADE_STATEMENTS = (
    "CREATE TABLE workflow_runs (\n\tid VARCHAR NOT NULL,\n\tstarted_at DATETIME NOT NULL,\n\tcompleted_at DATETIME,\n\tstatus VARCHAR(9) NOT NULL,\n\tis_mock BOOLEAN NOT NULL,\n\terror_message VARCHAR,\n\tPRIMARY KEY (id)\n)",
    "CREATE TABLE runs (\n\tid VARCHAR NOT NULL,\n\tworkflow_run_id VARCHAR NOT NULL,\n\tcandidate_snapshot_id VARCHAR,\n\tticker VARCHAR NOT NULL,\n\tcompany_name VARCHAR NOT NULL,\n\tstarted_at DATETIME NOT NULL,\n\tcompleted_at DATETIME,\n\tentry_path VARCHAR(8) NOT NULL,\n\tis_existing_position BOOLEAN NOT NULL,\n\tstatus VARCHAR(9) NOT NULL,\n\tis_mock BOOLEAN NOT NULL,\n\terror_message VARCHAR,\n\tfinal_rating VARCHAR,\n\tdecision_type VARCHAR(18),\n\trecommended_action VARCHAR,\n\tPRIMARY KEY (id),\n\tFOREIGN KEY(workflow_run_id) REFERENCES workflow_runs (id),\n\tFOREIGN KEY(candidate_snapshot_id) REFERENCES candidate_snapshots (id)\n)",
    "CREATE INDEX ix_runs_workflow_run_id ON runs (workflow_run_id)",
    "CREATE INDEX ix_runs_candidate_snapshot_id ON runs (candidate_snapshot_id)",
    "CREATE TABLE agent_executions (\n\tid VARCHAR NOT NULL,\n\trun_id VARCHAR NOT NULL,\n\tagent_name VARCHAR(10) NOT NULL,\n\tstatus VARCHAR(9) NOT NULL,\n\tstarted_at DATETIME,\n\tcompleted_at DATETIME,\n\terror_message VARCHAR,\n\tPRIMARY KEY (id),\n\tUNIQUE (run_id, agent_name),\n\tFOREIGN KEY(run_id) REFERENCES runs (id)\n)",
    "CREATE INDEX ix_agent_executions_run_id ON agent_executions (run_id)",
    "CREATE TABLE candidate_snapshots (\n\tid VARCHAR NOT NULL,\n\tworkflow_agent_execution_id VARCHAR,\n\tagent_execution_id VARCHAR,\n\tsort_order INTEGER NOT NULL,\n\tticker VARCHAR NOT NULL,\n\tcompany_name VARCHAR NOT NULL,\n\texchange VARCHAR NOT NULL,\n\tcurrency VARCHAR NOT NULL,\n\tmarket_cap_local INTEGER NOT NULL,\n\tmarket_cap_display VARCHAR NOT NULL,\n\tsector VARCHAR NOT NULL,\n\tindustry VARCHAR NOT NULL,\n\tanalyst_coverage_count INTEGER,\n\ttrailing_pe FLOAT,\n\tev_ebit FLOAT,\n\tprice_to_book FLOAT,\n\trevenue_growth_3y_cagr_pct FLOAT,\n\tfree_cash_flow_yield_pct FLOAT,\n\tnet_debt_to_ebitda FLOAT,\n\tpiotroski_f_score INTEGER,\n\taltman_z_score FLOAT,\n\tinsider_buying_last_6m BOOLEAN,\n\trationale VARCHAR NOT NULL,\n\tred_flags VARCHAR NOT NULL,\n\tdata_gaps VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tCHECK ((workflow_agent_execution_id IS NOT NULL) <> (agent_execution_id IS NOT NULL)),\n\tUNIQUE (workflow_agent_execution_id, sort_order),\n\tUNIQUE (agent_execution_id),\n\tFOREIGN KEY(workflow_agent_execution_id) REFERENCES workflow_agent_executions (id),\n\tFOREIGN KEY(agent_execution_id) REFERENCES agent_executions (id)\n)",
    "CREATE INDEX ix_candidate_snapshots_workflow_agent_execution_id ON candidate_snapshots (workflow_agent_execution_id)",
    "CREATE INDEX ix_candidate_snapshots_agent_execution_id ON candidate_snapshots (agent_execution_id)",
    "CREATE TABLE workflow_run_portfolio_tickers (\n\tid VARCHAR NOT NULL,\n\tworkflow_run_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tticker VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (workflow_run_id, sort_order),\n\tFOREIGN KEY(workflow_run_id) REFERENCES workflow_runs (id)\n)",
    "CREATE INDEX ix_workflow_run_portfolio_tickers_workflow_run_id ON workflow_run_portfolio_tickers (workflow_run_id)",
    "CREATE TABLE workflow_agent_executions (\n\tid VARCHAR NOT NULL,\n\tworkflow_run_id VARCHAR NOT NULL,\n\tagent_name VARCHAR(10) NOT NULL,\n\tstatus VARCHAR(9) NOT NULL,\n\tstarted_at DATETIME,\n\tcompleted_at DATETIME,\n\terror_message VARCHAR,\n\tPRIMARY KEY (id),\n\tUNIQUE (workflow_run_id, agent_name),\n\tFOREIGN KEY(workflow_run_id) REFERENCES workflow_runs (id)\n)",
    "CREATE INDEX ix_workflow_agent_executions_workflow_run_id ON workflow_agent_executions (workflow_run_id)",
    "CREATE TABLE research_reports (\n\tid VARCHAR NOT NULL,\n\tagent_execution_id VARCHAR NOT NULL,\n\tcandidate_snapshot_id VARCHAR NOT NULL,\n\texecutive_overview VARCHAR NOT NULL,\n\tproducts_and_services VARCHAR NOT NULL,\n\tcustomer_segments VARCHAR NOT NULL,\n\tunit_economics VARCHAR NOT NULL,\n\tcompetitive_positioning VARCHAR NOT NULL,\n\tmoat_and_durability VARCHAR NOT NULL,\n\tupdated_trailing_pe FLOAT,\n\tupdated_ev_ebit FLOAT,\n\tupdated_price_to_book FLOAT,\n\tupdated_revenue_growth_3y_cagr_pct FLOAT,\n\tupdated_free_cash_flow_yield_pct FLOAT,\n\tupdated_net_debt_to_ebitda FLOAT,\n\tupdated_piotroski_f_score INTEGER,\n\tupdated_altman_z_score FLOAT,\n\tupdated_insider_buying_last_6m BOOLEAN,\n\trevenue_and_growth_quality VARCHAR NOT NULL,\n\tprofitability_and_margin_structure VARCHAR NOT NULL,\n\tbalance_sheet_and_liquidity VARCHAR NOT NULL,\n\tcash_flow_and_capital_intensity VARCHAR NOT NULL,\n\tcapital_allocation VARCHAR NOT NULL,\n\tleadership_and_execution VARCHAR NOT NULL,\n\tgovernance_and_alignment VARCHAR NOT NULL,\n\tcommunication_quality VARCHAR NOT NULL,\n\tkey_concerns VARCHAR NOT NULL,\n\tdominant_narrative VARCHAR NOT NULL,\n\tbull_case_in_market VARCHAR NOT NULL,\n\tbear_case_in_market VARCHAR NOT NULL,\n\texpectations_implied_by_price VARCHAR NOT NULL,\n\twhere_expectations_may_be_wrong VARCHAR NOT NULL,\n\toriginal_data_gaps VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (agent_execution_id),\n\tFOREIGN KEY(agent_execution_id) REFERENCES agent_executions (id),\n\tFOREIGN KEY(candidate_snapshot_id) REFERENCES candidate_snapshots (id)\n)",
    "CREATE INDEX ix_research_reports_agent_execution_id ON research_reports (agent_execution_id)",
    "CREATE INDEX ix_research_reports_candidate_snapshot_id ON research_reports (candidate_snapshot_id)",
    "CREATE TABLE mispricing_theses (\n\tid VARCHAR NOT NULL,\n\tagent_execution_id VARCHAR NOT NULL,\n\tmispricing_type VARCHAR NOT NULL,\n\tmarket_belief VARCHAR NOT NULL,\n\tmispricing_argument VARCHAR NOT NULL,\n\tresolution_mechanism VARCHAR NOT NULL,\n\tconviction_level VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (agent_execution_id),\n\tFOREIGN KEY(agent_execution_id) REFERENCES agent_executions (id)\n)",
    "CREATE INDEX ix_mispricing_theses_agent_execution_id ON mispricing_theses (agent_execution_id)",
    "CREATE TABLE evaluation_reports (\n\tid VARCHAR NOT NULL,\n\tagent_execution_id VARCHAR NOT NULL,\n\tgovernance_concerns VARCHAR NOT NULL,\n\tbalance_sheet_stress VARCHAR NOT NULL,\n\tcustomer_or_supplier_concentration VARCHAR NOT NULL,\n\taccounting_quality VARCHAR NOT NULL,\n\trelated_party_transactions VARCHAR NOT NULL,\n\tlitigation_or_regulatory_risk VARCHAR NOT NULL,\n\toverall_red_flag_verdict VARCHAR NOT NULL,\n\tthesis_verdict VARCHAR NOT NULL,\n\tverdict_rationale VARCHAR NOT NULL,\n\tmaterial_data_gaps VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (agent_execution_id),\n\tFOREIGN KEY(agent_execution_id) REFERENCES agent_executions (id)\n)",
    "CREATE INDEX ix_evaluation_reports_agent_execution_id ON evaluation_reports (agent_execution_id)",
    "CREATE TABLE appraiser_reports (\n\tid VARCHAR NOT NULL,\n\tagent_execution_id VARCHAR NOT NULL,\n\tebit FLOAT NOT NULL,\n\trevenue FLOAT NOT NULL,\n\tcapital_expenditure FLOAT NOT NULL,\n\tn_shares_outstanding FLOAT NOT NULL,\n\tmarket_cap FLOAT NOT NULL,\n\tgross_debt FLOAT NOT NULL,\n\tgross_debt_last_year FLOAT NOT NULL,\n\tnet_debt FLOAT NOT NULL,\n\ttotal_interest_expense FLOAT NOT NULL,\n\tbeta FLOAT NOT NULL,\n\treasoning VARCHAR NOT NULL,\n\tforecast_period_years INTEGER NOT NULL,\n\tassumed_tax_rate FLOAT NOT NULL,\n\tassumed_forecast_period_annual_revenue_growth_rate FLOAT NOT NULL,\n\tassumed_perpetuity_cash_flow_growth_rate FLOAT NOT NULL,\n\tassumed_ebit_margin FLOAT NOT NULL,\n\tassumed_depreciation_and_amortization_rate FLOAT NOT NULL,\n\tassumed_capex_rate FLOAT NOT NULL,\n\tassumed_change_in_working_capital_rate FLOAT NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (agent_execution_id),\n\tFOREIGN KEY(agent_execution_id) REFERENCES agent_executions (id)\n)",
    "CREATE INDEX ix_appraiser_reports_agent_execution_id ON appraiser_reports (agent_execution_id)",
    "CREATE TABLE dcf_valuations (\n\tid VARCHAR NOT NULL,\n\trun_id VARCHAR NOT NULL,\n\tappraiser_agent_execution_id VARCHAR NOT NULL,\n\tintrinsic_share_price FLOAT NOT NULL,\n\tenterprise_value FLOAT NOT NULL,\n\tequity_value FLOAT NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (run_id),\n\tUNIQUE (appraiser_agent_execution_id),\n\tFOREIGN KEY(run_id) REFERENCES runs (id),\n\tFOREIGN KEY(appraiser_agent_execution_id) REFERENCES agent_executions (id)\n)",
    "CREATE INDEX ix_dcf_valuations_appraiser_agent_execution_id ON dcf_valuations (appraiser_agent_execution_id)",
    "CREATE INDEX ix_dcf_valuations_run_id ON dcf_valuations (run_id)",
    "CREATE TABLE run_final_decisions (\n\tid VARCHAR NOT NULL,\n\trun_id VARCHAR NOT NULL,\n\tsource_agent_execution_id VARCHAR NOT NULL,\n\tdecision_type VARCHAR(18) NOT NULL,\n\tdecision_date DATE NOT NULL,\n\tis_existing_position BOOLEAN NOT NULL,\n\trating VARCHAR NOT NULL,\n\trecommended_action VARCHAR NOT NULL,\n\tconviction VARCHAR,\n\trejection_reason VARCHAR,\n\tcurrent_price FLOAT,\n\tbear_intrinsic_value FLOAT,\n\tbase_intrinsic_value FLOAT,\n\tbull_intrinsic_value FLOAT,\n\tmargin_of_safety_base_pct FLOAT,\n\tmargin_of_safety_verdict VARCHAR,\n\tprimary_driver VARCHAR,\n\tred_flag_disposition VARCHAR,\n\tdata_gap_disposition VARCHAR,\n\tthesis_expiry_note VARCHAR,\n\tPRIMARY KEY (id),\n\tUNIQUE (run_id),\n\tCHECK (\n            (\n                decision_type = 'arbiter'\n                AND rejection_reason IS NULL\n                AND conviction IS NOT NULL\n                AND current_price IS NOT NULL\n                AND bear_intrinsic_value IS NOT NULL\n                AND base_intrinsic_value IS NOT NULL\n                AND bull_intrinsic_value IS NOT NULL\n                AND margin_of_safety_base_pct IS NOT NULL\n                AND margin_of_safety_verdict IS NOT NULL\n                AND primary_driver IS NOT NULL\n                AND red_flag_disposition IS NOT NULL\n                AND data_gap_disposition IS NOT NULL\n                AND thesis_expiry_note IS NOT NULL\n            )\n            OR\n            (\n                decision_type = 'sentinel_rejection'\n                AND rejection_reason IS NOT NULL\n                AND conviction IS NULL\n                AND current_price IS NULL\n                AND bear_intrinsic_value IS NULL\n                AND base_intrinsic_value IS NULL\n                AND bull_intrinsic_value IS NULL\n                AND margin_of_safety_base_pct IS NULL\n                AND margin_of_safety_verdict IS NULL\n                AND primary_driver IS NULL\n                AND red_flag_disposition IS NULL\n                AND data_gap_disposition IS NULL\n                AND thesis_expiry_note IS NULL\n            )\n            ),\n\tFOREIGN KEY(run_id) REFERENCES runs (id),\n\tFOREIGN KEY(source_agent_execution_id) REFERENCES agent_executions (id)\n)",
    "CREATE INDEX ix_run_final_decisions_source_agent_execution_id ON run_final_decisions (source_agent_execution_id)",
    "CREATE INDEX ix_run_final_decisions_run_id ON run_final_decisions (run_id)",
    "CREATE TABLE research_report_narrative_monitoring_signals (\n\tid VARCHAR NOT NULL,\n\tresearch_report_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tsignal VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (research_report_id, sort_order),\n\tFOREIGN KEY(research_report_id) REFERENCES research_reports (id)\n)",
    "CREATE INDEX ix_research_report_narrative_monitoring_signals_research_report_id ON research_report_narrative_monitoring_signals (research_report_id)",
    "CREATE TABLE research_report_risks (\n\tid VARCHAR NOT NULL,\n\tresearch_report_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\trisk VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (research_report_id, sort_order),\n\tFOREIGN KEY(research_report_id) REFERENCES research_reports (id)\n)",
    "CREATE INDEX ix_research_report_risks_research_report_id ON research_report_risks (research_report_id)",
    "CREATE TABLE research_report_potential_catalysts (\n\tid VARCHAR NOT NULL,\n\tresearch_report_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tcatalyst VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (research_report_id, sort_order),\n\tFOREIGN KEY(research_report_id) REFERENCES research_reports (id)\n)",
    "CREATE INDEX ix_research_report_potential_catalysts_research_report_id ON research_report_potential_catalysts (research_report_id)",
    "CREATE TABLE research_report_closed_gaps (\n\tid VARCHAR NOT NULL,\n\tresearch_report_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tgap_text VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (research_report_id, sort_order),\n\tFOREIGN KEY(research_report_id) REFERENCES research_reports (id)\n)",
    "CREATE INDEX ix_research_report_closed_gaps_research_report_id ON research_report_closed_gaps (research_report_id)",
    "CREATE TABLE research_report_remaining_open_gaps (\n\tid VARCHAR NOT NULL,\n\tresearch_report_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tgap_text VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (research_report_id, sort_order),\n\tFOREIGN KEY(research_report_id) REFERENCES research_reports (id)\n)",
    "CREATE INDEX ix_research_report_remaining_open_gaps_research_report_id ON research_report_remaining_open_gaps (research_report_id)",
    "CREATE TABLE research_report_material_open_gaps (\n\tid VARCHAR NOT NULL,\n\tresearch_report_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tgap_text VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (research_report_id, sort_order),\n\tFOREIGN KEY(research_report_id) REFERENCES research_reports (id)\n)",
    "CREATE INDEX ix_research_report_material_open_gaps_research_report_id ON research_report_material_open_gaps (research_report_id)",
    "CREATE TABLE research_report_source_notes (\n\tid VARCHAR NOT NULL,\n\tresearch_report_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tsource_note VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (research_report_id, sort_order),\n\tFOREIGN KEY(research_report_id) REFERENCES research_reports (id)\n)",
    "CREATE INDEX ix_research_report_source_notes_research_report_id ON research_report_source_notes (research_report_id)",
    "CREATE TABLE mispricing_thesis_falsification_conditions (\n\tid VARCHAR NOT NULL,\n\tmispricing_thesis_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tcondition_text VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (mispricing_thesis_id, sort_order),\n\tFOREIGN KEY(mispricing_thesis_id) REFERENCES mispricing_theses (id)\n)",
    "CREATE INDEX ix_mispricing_thesis_falsification_conditions_mispricing_thesis_id ON mispricing_thesis_falsification_conditions (mispricing_thesis_id)",
    "CREATE TABLE mispricing_thesis_risks (\n\tid VARCHAR NOT NULL,\n\tmispricing_thesis_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\trisk_text VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (mispricing_thesis_id, sort_order),\n\tFOREIGN KEY(mispricing_thesis_id) REFERENCES mispricing_theses (id)\n)",
    "CREATE INDEX ix_mispricing_thesis_risks_mispricing_thesis_id ON mispricing_thesis_risks (mispricing_thesis_id)",
    "CREATE TABLE mispricing_thesis_evaluation_questions (\n\tid VARCHAR NOT NULL,\n\tmispricing_thesis_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tquestion_text VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (mispricing_thesis_id, sort_order),\n\tFOREIGN KEY(mispricing_thesis_id) REFERENCES mispricing_theses (id)\n)",
    "CREATE INDEX ix_mispricing_thesis_evaluation_questions_mispricing_thesis_id ON mispricing_thesis_evaluation_questions (mispricing_thesis_id)",
    "CREATE TABLE mispricing_thesis_permanent_loss_scenarios (\n\tid VARCHAR NOT NULL,\n\tmispricing_thesis_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tscenario_text VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (mispricing_thesis_id, sort_order),\n\tFOREIGN KEY(mispricing_thesis_id) REFERENCES mispricing_theses (id)\n)",
    "CREATE INDEX ix_mispricing_thesis_permanent_loss_scenarios_mispricing_thesis_id ON mispricing_thesis_permanent_loss_scenarios (mispricing_thesis_id)",
    "CREATE TABLE evaluation_question_assessments (\n\tid VARCHAR NOT NULL,\n\tevaluation_report_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tquestion VARCHAR NOT NULL,\n\tevidence VARCHAR NOT NULL,\n\tverdict VARCHAR NOT NULL,\n\tconfidence VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (evaluation_report_id, sort_order),\n\tFOREIGN KEY(evaluation_report_id) REFERENCES evaluation_reports (id)\n)",
    "CREATE INDEX ix_evaluation_question_assessments_evaluation_report_id ON evaluation_question_assessments (evaluation_report_id)",
    "CREATE TABLE evaluation_caveats (\n\tid VARCHAR NOT NULL,\n\tevaluation_report_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tcaveat VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (evaluation_report_id, sort_order),\n\tFOREIGN KEY(evaluation_report_id) REFERENCES evaluation_reports (id)\n)",
    "CREATE INDEX ix_evaluation_caveats_evaluation_report_id ON evaluation_caveats (evaluation_report_id)",
    "CREATE TABLE run_final_decision_supporting_factors (\n\tid VARCHAR NOT NULL,\n\trun_final_decision_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tfactor_text VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (run_final_decision_id, sort_order),\n\tFOREIGN KEY(run_final_decision_id) REFERENCES run_final_decisions (id)\n)",
    "CREATE INDEX ix_run_final_decision_supporting_factors_run_final_decision_id ON run_final_decision_supporting_factors (run_final_decision_id)",
    "CREATE TABLE run_final_decision_mitigating_factors (\n\tid VARCHAR NOT NULL,\n\trun_final_decision_id VARCHAR NOT NULL,\n\tsort_order INTEGER NOT NULL,\n\tfactor_text VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (run_final_decision_id, sort_order),\n\tFOREIGN KEY(run_final_decision_id) REFERENCES run_final_decisions (id)\n)",
    "CREATE INDEX ix_run_final_decision_mitigating_factors_run_final_decision_id ON run_final_decision_mitigating_factors (run_final_decision_id)",
    "CREATE TABLE agent_conversations (\n\tid VARCHAR NOT NULL,\n\tworkflow_agent_execution_id VARCHAR,\n\tagent_execution_id VARCHAR,\n\tsystem_prompt VARCHAR NOT NULL,\n\tPRIMARY KEY (id),\n\tCHECK ((workflow_agent_execution_id IS NOT NULL) <> (agent_execution_id IS NOT NULL)),\n\tUNIQUE (workflow_agent_execution_id),\n\tUNIQUE (agent_execution_id),\n\tFOREIGN KEY(workflow_agent_execution_id) REFERENCES workflow_agent_executions (id),\n\tFOREIGN KEY(agent_execution_id) REFERENCES agent_executions (id)\n)",
    "CREATE INDEX ix_agent_conversations_agent_execution_id ON agent_conversations (agent_execution_id)",
    "CREATE INDEX ix_agent_conversations_workflow_agent_execution_id ON agent_conversations (workflow_agent_execution_id)",
    "CREATE TABLE agent_conversation_messages (\n\tid VARCHAR NOT NULL,\n\tconversation_id VARCHAR NOT NULL,\n\tmessage_index INTEGER NOT NULL,\n\tmessage_kind VARCHAR(8) NOT NULL,\n\tPRIMARY KEY (id),\n\tUNIQUE (conversation_id, message_index),\n\tFOREIGN KEY(conversation_id) REFERENCES agent_conversations (id)\n)",
    "CREATE INDEX ix_agent_conversation_messages_conversation_id ON agent_conversation_messages (conversation_id)",
    "CREATE TABLE agent_conversation_message_parts (\n\tid VARCHAR NOT NULL,\n\tconversation_message_id VARCHAR NOT NULL,\n\tpart_index INTEGER NOT NULL,\n\tpart_kind VARCHAR(13) NOT NULL,\n\tcontent_text VARCHAR,\n\ttool_name VARCHAR,\n\ttool_call_id VARCHAR,\n\tPRIMARY KEY (id),\n\tUNIQUE (conversation_message_id, part_index),\n\tCHECK (\n            (\n                part_kind IN ('system_prompt', 'user_prompt', 'text', 'retry_prompt')\n                AND content_text IS NOT NULL\n            )\n            OR\n            (\n                part_kind = 'tool_call'\n                AND tool_name IS NOT NULL\n                AND tool_call_id IS NOT NULL\n            )\n            OR\n            (\n                part_kind = 'tool_return'\n                AND content_text IS NOT NULL\n                AND tool_name IS NOT NULL\n                AND tool_call_id IS NOT NULL\n            )\n            ),\n\tFOREIGN KEY(conversation_message_id) REFERENCES agent_conversation_messages (id)\n)",
    "CREATE INDEX ix_agent_conversation_message_parts_conversation_message_id ON agent_conversation_message_parts (conversation_message_id)",
)


_DOWNGRADE_TABLES = (
    "agent_conversation_message_parts",
    "agent_conversation_messages",
    "agent_conversations",
    "run_final_decision_mitigating_factors",
    "run_final_decision_supporting_factors",
    "evaluation_caveats",
    "evaluation_question_assessments",
    "mispricing_thesis_permanent_loss_scenarios",
    "mispricing_thesis_evaluation_questions",
    "mispricing_thesis_risks",
    "mispricing_thesis_falsification_conditions",
    "research_report_source_notes",
    "research_report_material_open_gaps",
    "research_report_remaining_open_gaps",
    "research_report_closed_gaps",
    "research_report_potential_catalysts",
    "research_report_risks",
    "research_report_narrative_monitoring_signals",
    "run_final_decisions",
    "dcf_valuations",
    "appraiser_reports",
    "evaluation_reports",
    "mispricing_theses",
    "research_reports",
    "workflow_agent_executions",
    "workflow_run_portfolio_tickers",
    "candidate_snapshots",
    "agent_executions",
    "runs",
    "workflow_runs",
)


def upgrade() -> None:
    for statement in _UPGRADE_STATEMENTS:
        op.execute(text(statement))


def downgrade() -> None:
    for table_name in _DOWNGRADE_TABLES:
        op.drop_table(table_name)
