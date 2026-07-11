"""Unify workflow and lane agent executions into one ``agent_executions`` table.

Copies ``workflow_agent_executions`` into ``agent_executions`` (preserving IDs),
rebuilds ``candidate_snapshots`` and ``agent_conversations`` onto a single
``agent_execution_id`` FK, then drops ``workflow_agent_executions``.

Revision ID: 0010_unify_agent_executions
Revises: 0009_run_lane_aborted
Create Date: 2026-07-11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_unify_agent_executions"
down_revision = "0009_run_lane_aborted"
branch_labels = None
depends_on = None

_CANDIDATE_SNAPSHOT_COLUMNS = """
    id,
    agent_execution_id,
    sort_order,
    ticker,
    company_name,
    exchange,
    currency,
    market_cap_local,
    market_cap_display,
    sector,
    industry,
    analyst_coverage_count,
    trailing_pe,
    ev_ebit,
    price_to_book,
    revenue_growth_3y_cagr_pct,
    free_cash_flow_yield_pct,
    net_debt_to_ebitda,
    piotroski_f_score,
    altman_z_score,
    insider_buying_last_6m,
    resolved_ticker,
    resolution_notes,
    gate_status,
    gate_failure_reason,
    is_actively_trading,
    gate_probed_at,
    gate_data_source,
    rationale,
    red_flags,
    data_gaps
"""


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys=OFF"))

    collision = conn.execute(
        sa.text(
            """
            SELECT wae.id
            FROM workflow_agent_executions AS wae
            INNER JOIN agent_executions AS ae ON ae.id = wae.id
            LIMIT 1
            """
        )
    ).fetchone()
    if collision is not None:
        raise RuntimeError(
            f"Cannot unify agent executions: ID collision on {collision[0]!r}"
        )

    conn.execute(
        sa.text(
            """
            CREATE TABLE agent_executions_new (
                id VARCHAR NOT NULL,
                workflow_run_id VARCHAR,
                run_id VARCHAR,
                agent_name VARCHAR(10) NOT NULL,
                status VARCHAR(9) NOT NULL,
                started_at DATETIME,
                completed_at DATETIME,
                error_message VARCHAR,
                model_name VARCHAR,
                PRIMARY KEY (id),
                CHECK ((workflow_run_id IS NOT NULL) <> (run_id IS NOT NULL)),
                UNIQUE (workflow_run_id, agent_name),
                UNIQUE (run_id, agent_name),
                FOREIGN KEY(workflow_run_id) REFERENCES workflow_runs (id),
                FOREIGN KEY(run_id) REFERENCES runs (id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO agent_executions_new (
                id,
                workflow_run_id,
                run_id,
                agent_name,
                status,
                started_at,
                completed_at,
                error_message,
                model_name
            )
            SELECT
                id,
                NULL,
                run_id,
                agent_name,
                status,
                started_at,
                completed_at,
                error_message,
                model_name
            FROM agent_executions
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO agent_executions_new (
                id,
                workflow_run_id,
                run_id,
                agent_name,
                status,
                started_at,
                completed_at,
                error_message,
                model_name
            )
            SELECT
                id,
                workflow_run_id,
                NULL,
                agent_name,
                status,
                started_at,
                completed_at,
                error_message,
                model_name
            FROM workflow_agent_executions
            """
        )
    )
    conn.execute(sa.text("DROP TABLE agent_executions"))
    conn.execute(sa.text("ALTER TABLE agent_executions_new RENAME TO agent_executions"))
    conn.execute(
        sa.text("CREATE INDEX ix_agent_executions_run_id ON agent_executions (run_id)")
    )
    conn.execute(
        sa.text(
            "CREATE INDEX ix_agent_executions_workflow_run_id "
            "ON agent_executions (workflow_run_id)"
        )
    )

    conn.execute(
        sa.text(
            """
            CREATE TABLE candidate_snapshots_new (
                id VARCHAR NOT NULL,
                agent_execution_id VARCHAR NOT NULL,
                sort_order INTEGER NOT NULL,
                ticker VARCHAR NOT NULL,
                company_name VARCHAR NOT NULL,
                exchange VARCHAR NOT NULL,
                currency VARCHAR NOT NULL,
                market_cap_local INTEGER NOT NULL,
                market_cap_display VARCHAR NOT NULL,
                sector VARCHAR NOT NULL,
                industry VARCHAR NOT NULL,
                analyst_coverage_count INTEGER,
                trailing_pe FLOAT,
                ev_ebit FLOAT,
                price_to_book FLOAT,
                revenue_growth_3y_cagr_pct FLOAT,
                free_cash_flow_yield_pct FLOAT,
                net_debt_to_ebitda FLOAT,
                piotroski_f_score INTEGER,
                altman_z_score FLOAT,
                insider_buying_last_6m BOOLEAN,
                resolved_ticker VARCHAR,
                resolution_notes VARCHAR,
                gate_status VARCHAR,
                gate_failure_reason VARCHAR,
                is_actively_trading BOOLEAN,
                gate_probed_at DATETIME,
                gate_data_source VARCHAR,
                rationale VARCHAR NOT NULL,
                red_flags VARCHAR NOT NULL,
                data_gaps VARCHAR NOT NULL,
                PRIMARY KEY (id),
                UNIQUE (agent_execution_id, sort_order),
                FOREIGN KEY(agent_execution_id) REFERENCES agent_executions (id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            f"""
            INSERT INTO candidate_snapshots_new (
                {_CANDIDATE_SNAPSHOT_COLUMNS}
            )
            SELECT
                id,
                COALESCE(agent_execution_id, workflow_agent_execution_id),
                sort_order,
                ticker,
                company_name,
                exchange,
                currency,
                market_cap_local,
                market_cap_display,
                sector,
                industry,
                analyst_coverage_count,
                trailing_pe,
                ev_ebit,
                price_to_book,
                revenue_growth_3y_cagr_pct,
                free_cash_flow_yield_pct,
                net_debt_to_ebitda,
                piotroski_f_score,
                altman_z_score,
                insider_buying_last_6m,
                resolved_ticker,
                resolution_notes,
                gate_status,
                gate_failure_reason,
                is_actively_trading,
                gate_probed_at,
                gate_data_source,
                rationale,
                red_flags,
                data_gaps
            FROM candidate_snapshots
            """
        )
    )
    conn.execute(sa.text("DROP TABLE candidate_snapshots"))
    conn.execute(
        sa.text("ALTER TABLE candidate_snapshots_new RENAME TO candidate_snapshots")
    )
    conn.execute(
        sa.text(
            "CREATE INDEX ix_candidate_snapshots_agent_execution_id "
            "ON candidate_snapshots (agent_execution_id)"
        )
    )

    conn.execute(
        sa.text(
            """
            CREATE TABLE agent_conversations_new (
                id VARCHAR NOT NULL,
                agent_execution_id VARCHAR NOT NULL,
                system_prompt VARCHAR NOT NULL,
                PRIMARY KEY (id),
                UNIQUE (agent_execution_id),
                FOREIGN KEY(agent_execution_id) REFERENCES agent_executions (id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO agent_conversations_new (
                id,
                agent_execution_id,
                system_prompt
            )
            SELECT
                id,
                COALESCE(agent_execution_id, workflow_agent_execution_id),
                system_prompt
            FROM agent_conversations
            """
        )
    )
    conn.execute(sa.text("DROP TABLE agent_conversations"))
    conn.execute(
        sa.text("ALTER TABLE agent_conversations_new RENAME TO agent_conversations")
    )
    conn.execute(
        sa.text(
            "CREATE INDEX ix_agent_conversations_agent_execution_id "
            "ON agent_conversations (agent_execution_id)"
        )
    )

    conn.execute(sa.text("DROP TABLE workflow_agent_executions"))

    conn.execute(sa.text("PRAGMA foreign_keys=ON"))

    orphan_snapshots = conn.execute(
        sa.text(
            """
            SELECT COUNT(*) FROM candidate_snapshots AS cs
            WHERE NOT EXISTS (
                SELECT 1 FROM agent_executions AS ae WHERE ae.id = cs.agent_execution_id
            )
            """
        )
    ).scalar()
    if orphan_snapshots:
        raise RuntimeError(
            f"Unify agent executions left {orphan_snapshots} orphan candidate_snapshots"
        )
    orphan_conversations = conn.execute(
        sa.text(
            """
            SELECT COUNT(*) FROM agent_conversations AS ac
            WHERE NOT EXISTS (
                SELECT 1 FROM agent_executions AS ae WHERE ae.id = ac.agent_execution_id
            )
            """
        )
    ).scalar()
    if orphan_conversations:
        raise RuntimeError(
            "Unify agent executions left "
            f"{orphan_conversations} orphan agent_conversations"
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys=OFF"))

    conn.execute(
        sa.text(
            """
            CREATE TABLE workflow_agent_executions (
                id VARCHAR NOT NULL,
                workflow_run_id VARCHAR NOT NULL,
                agent_name VARCHAR(10) NOT NULL,
                status VARCHAR(9) NOT NULL,
                started_at DATETIME,
                completed_at DATETIME,
                error_message VARCHAR,
                model_name VARCHAR,
                PRIMARY KEY (id),
                UNIQUE (workflow_run_id, agent_name),
                FOREIGN KEY(workflow_run_id) REFERENCES workflow_runs (id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX ix_workflow_agent_executions_workflow_run_id "
            "ON workflow_agent_executions (workflow_run_id)"
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO workflow_agent_executions (
                id,
                workflow_run_id,
                agent_name,
                status,
                started_at,
                completed_at,
                error_message,
                model_name
            )
            SELECT
                id,
                workflow_run_id,
                agent_name,
                status,
                started_at,
                completed_at,
                error_message,
                model_name
            FROM agent_executions
            WHERE workflow_run_id IS NOT NULL
            """
        )
    )

    conn.execute(
        sa.text(
            """
            CREATE TABLE agent_conversations_old (
                id VARCHAR NOT NULL,
                workflow_agent_execution_id VARCHAR,
                agent_execution_id VARCHAR,
                system_prompt VARCHAR NOT NULL,
                PRIMARY KEY (id),
                CHECK (
                    (workflow_agent_execution_id IS NOT NULL)
                    <> (agent_execution_id IS NOT NULL)
                ),
                UNIQUE (workflow_agent_execution_id),
                UNIQUE (agent_execution_id),
                FOREIGN KEY(workflow_agent_execution_id)
                    REFERENCES workflow_agent_executions (id),
                FOREIGN KEY(agent_execution_id) REFERENCES agent_executions (id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO agent_conversations_old (
                id,
                workflow_agent_execution_id,
                agent_execution_id,
                system_prompt
            )
            SELECT
                ac.id,
                CASE
                    WHEN ae.workflow_run_id IS NOT NULL THEN ac.agent_execution_id
                    ELSE NULL
                END,
                CASE
                    WHEN ae.run_id IS NOT NULL THEN ac.agent_execution_id
                    ELSE NULL
                END,
                ac.system_prompt
            FROM agent_conversations AS ac
            JOIN agent_executions AS ae ON ae.id = ac.agent_execution_id
            """
        )
    )
    conn.execute(sa.text("DROP TABLE agent_conversations"))
    conn.execute(
        sa.text("ALTER TABLE agent_conversations_old RENAME TO agent_conversations")
    )
    conn.execute(
        sa.text(
            "CREATE INDEX ix_agent_conversations_agent_execution_id "
            "ON agent_conversations (agent_execution_id)"
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX ix_agent_conversations_workflow_agent_execution_id "
            "ON agent_conversations (workflow_agent_execution_id)"
        )
    )

    conn.execute(
        sa.text(
            """
            CREATE TABLE candidate_snapshots_old (
                id VARCHAR NOT NULL,
                workflow_agent_execution_id VARCHAR,
                agent_execution_id VARCHAR,
                sort_order INTEGER NOT NULL,
                ticker VARCHAR NOT NULL,
                company_name VARCHAR NOT NULL,
                exchange VARCHAR NOT NULL,
                currency VARCHAR NOT NULL,
                market_cap_local INTEGER NOT NULL,
                market_cap_display VARCHAR NOT NULL,
                sector VARCHAR NOT NULL,
                industry VARCHAR NOT NULL,
                analyst_coverage_count INTEGER,
                trailing_pe FLOAT,
                ev_ebit FLOAT,
                price_to_book FLOAT,
                revenue_growth_3y_cagr_pct FLOAT,
                free_cash_flow_yield_pct FLOAT,
                net_debt_to_ebitda FLOAT,
                piotroski_f_score INTEGER,
                altman_z_score FLOAT,
                insider_buying_last_6m BOOLEAN,
                resolved_ticker VARCHAR,
                resolution_notes VARCHAR,
                gate_status VARCHAR,
                gate_failure_reason VARCHAR,
                is_actively_trading BOOLEAN,
                gate_probed_at DATETIME,
                gate_data_source VARCHAR,
                rationale VARCHAR NOT NULL,
                red_flags VARCHAR NOT NULL,
                data_gaps VARCHAR NOT NULL,
                PRIMARY KEY (id),
                CHECK (
                    (workflow_agent_execution_id IS NOT NULL)
                    <> (agent_execution_id IS NOT NULL)
                ),
                UNIQUE (workflow_agent_execution_id, sort_order),
                UNIQUE (agent_execution_id),
                FOREIGN KEY(workflow_agent_execution_id)
                    REFERENCES workflow_agent_executions (id),
                FOREIGN KEY(agent_execution_id) REFERENCES agent_executions (id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO candidate_snapshots_old (
                id,
                workflow_agent_execution_id,
                agent_execution_id,
                sort_order,
                ticker,
                company_name,
                exchange,
                currency,
                market_cap_local,
                market_cap_display,
                sector,
                industry,
                analyst_coverage_count,
                trailing_pe,
                ev_ebit,
                price_to_book,
                revenue_growth_3y_cagr_pct,
                free_cash_flow_yield_pct,
                net_debt_to_ebitda,
                piotroski_f_score,
                altman_z_score,
                insider_buying_last_6m,
                resolved_ticker,
                resolution_notes,
                gate_status,
                gate_failure_reason,
                is_actively_trading,
                gate_probed_at,
                gate_data_source,
                rationale,
                red_flags,
                data_gaps
            )
            SELECT
                cs.id,
                CASE
                    WHEN ae.workflow_run_id IS NOT NULL THEN cs.agent_execution_id
                    ELSE NULL
                END,
                CASE
                    WHEN ae.run_id IS NOT NULL THEN cs.agent_execution_id
                    ELSE NULL
                END,
                cs.sort_order,
                cs.ticker,
                cs.company_name,
                cs.exchange,
                cs.currency,
                cs.market_cap_local,
                cs.market_cap_display,
                cs.sector,
                cs.industry,
                cs.analyst_coverage_count,
                cs.trailing_pe,
                cs.ev_ebit,
                cs.price_to_book,
                cs.revenue_growth_3y_cagr_pct,
                cs.free_cash_flow_yield_pct,
                cs.net_debt_to_ebitda,
                cs.piotroski_f_score,
                cs.altman_z_score,
                cs.insider_buying_last_6m,
                cs.resolved_ticker,
                cs.resolution_notes,
                cs.gate_status,
                cs.gate_failure_reason,
                cs.is_actively_trading,
                cs.gate_probed_at,
                cs.gate_data_source,
                cs.rationale,
                cs.red_flags,
                cs.data_gaps
            FROM candidate_snapshots AS cs
            JOIN agent_executions AS ae ON ae.id = cs.agent_execution_id
            """
        )
    )
    conn.execute(sa.text("DROP TABLE candidate_snapshots"))
    conn.execute(
        sa.text("ALTER TABLE candidate_snapshots_old RENAME TO candidate_snapshots")
    )
    conn.execute(
        sa.text(
            "CREATE INDEX ix_candidate_snapshots_agent_execution_id "
            "ON candidate_snapshots (agent_execution_id)"
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX ix_candidate_snapshots_workflow_agent_execution_id "
            "ON candidate_snapshots (workflow_agent_execution_id)"
        )
    )

    conn.execute(
        sa.text(
            """
            CREATE TABLE agent_executions_old (
                id VARCHAR NOT NULL,
                run_id VARCHAR NOT NULL,
                agent_name VARCHAR(10) NOT NULL,
                status VARCHAR(9) NOT NULL,
                started_at DATETIME,
                completed_at DATETIME,
                error_message VARCHAR,
                model_name VARCHAR,
                PRIMARY KEY (id),
                UNIQUE (run_id, agent_name),
                FOREIGN KEY(run_id) REFERENCES runs (id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO agent_executions_old (
                id,
                run_id,
                agent_name,
                status,
                started_at,
                completed_at,
                error_message,
                model_name
            )
            SELECT
                id,
                run_id,
                agent_name,
                status,
                started_at,
                completed_at,
                error_message,
                model_name
            FROM agent_executions
            WHERE run_id IS NOT NULL
            """
        )
    )
    conn.execute(sa.text("DROP TABLE agent_executions"))
    conn.execute(sa.text("ALTER TABLE agent_executions_old RENAME TO agent_executions"))
    conn.execute(
        sa.text("CREATE INDEX ix_agent_executions_run_id ON agent_executions (run_id)")
    )

    conn.execute(sa.text("PRAGMA foreign_keys=ON"))
