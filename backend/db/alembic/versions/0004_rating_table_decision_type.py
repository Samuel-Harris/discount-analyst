"""Add ``rating_table`` final decision type; normalise legacy ``arbiter`` rows; tighten CHECK; drop arbiter executions.

Historical ``run_final_decisions`` rows with ``decision_type = 'arbiter'`` are rewritten to
``rating_table`` when copied into the recreated table (the pre-migration CHECK still names
``arbiter``, so in-place ``UPDATE`` on the old table is not possible). ``runs.decision_type``
values ``arbiter`` are updated to ``rating_table`` before the rebuild.

Revision ID: 0004_rating_table_decision_type
Revises: 0003_appraiser_reports_assumption_pct_columns
Create Date: 2026-05-17

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004_rating_table_decision_type"
down_revision = "0003_appraiser_reports_assumption_pct_columns"
branch_labels = None
depends_on = None

_RFD_CHECK = """
(
    decision_type = 'rating_table'
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


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys=OFF"))

    conn.execute(
        sa.text(
            """
            UPDATE run_final_decisions AS rfd
            SET source_agent_execution_id = COALESCE(
                (
                    SELECT ae.id FROM agent_executions AS ae
                    WHERE ae.run_id = rfd.run_id AND ae.agent_name = 'appraiser'
                    LIMIT 1
                ),
                (
                    SELECT ae.id FROM agent_executions AS ae
                    WHERE ae.run_id = rfd.run_id AND ae.agent_name = 'sentinel'
                    LIMIT 1
                ),
                (
                    SELECT ae.id FROM agent_executions AS ae
                    WHERE ae.run_id = rfd.run_id AND ae.agent_name != 'arbiter'
                    LIMIT 1
                )
            )
            WHERE rfd.decision_type = 'arbiter'
            """
        )
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM run_final_decisions
            WHERE decision_type = 'arbiter'
            AND NOT EXISTS (
                SELECT 1 FROM agent_executions AS ae
                WHERE ae.run_id = run_final_decisions.run_id
                AND ae.agent_name != 'arbiter'
            )
            """
        )
    )

    conn.execute(
        sa.text(
            """
            UPDATE runs
            SET decision_type = 'rating_table'
            WHERE decision_type = 'arbiter'
            """
        )
    )

    conn.execute(
        sa.text(
            """
            DELETE FROM agent_conversation_message_parts
            WHERE conversation_message_id IN (
                SELECT acm.id FROM agent_conversation_messages AS acm
                JOIN agent_conversations AS ac ON ac.id = acm.conversation_id
                JOIN agent_executions AS ae ON ae.id = ac.agent_execution_id
                WHERE ae.agent_name = 'arbiter'
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM agent_conversation_messages
            WHERE conversation_id IN (
                SELECT ac.id FROM agent_conversations AS ac
                JOIN agent_executions AS ae ON ae.id = ac.agent_execution_id
                WHERE ae.agent_name = 'arbiter'
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM agent_conversations
            WHERE agent_execution_id IN (
                SELECT id FROM agent_executions WHERE agent_name = 'arbiter'
            )
            """
        )
    )
    conn.execute(sa.text("DELETE FROM agent_executions WHERE agent_name = 'arbiter'"))

    conn.execute(
        sa.text("CREATE TABLE _rfd_backup AS SELECT * FROM run_final_decisions")
    )
    conn.execute(
        sa.text(
            "CREATE TABLE _rfdsf_backup AS SELECT * FROM run_final_decision_supporting_factors"
        )
    )
    conn.execute(
        sa.text(
            "CREATE TABLE _rfdmf_backup AS SELECT * FROM run_final_decision_mitigating_factors"
        )
    )

    conn.execute(sa.text("DROP TABLE run_final_decision_supporting_factors"))
    conn.execute(sa.text("DROP TABLE run_final_decision_mitigating_factors"))
    conn.execute(sa.text("DROP TABLE run_final_decisions"))

    conn.execute(
        sa.text(
            f"""
            CREATE TABLE run_final_decisions (
                id VARCHAR NOT NULL,
                run_id VARCHAR NOT NULL,
                source_agent_execution_id VARCHAR NOT NULL,
                decision_type VARCHAR(18) NOT NULL,
                decision_date DATE NOT NULL,
                is_existing_position BOOLEAN NOT NULL,
                rating VARCHAR NOT NULL,
                recommended_action VARCHAR NOT NULL,
                conviction VARCHAR,
                rejection_reason VARCHAR,
                current_price FLOAT,
                bear_intrinsic_value FLOAT,
                base_intrinsic_value FLOAT,
                bull_intrinsic_value FLOAT,
                margin_of_safety_base_pct FLOAT,
                margin_of_safety_verdict VARCHAR,
                primary_driver VARCHAR,
                red_flag_disposition VARCHAR,
                data_gap_disposition VARCHAR,
                thesis_expiry_note VARCHAR,
                PRIMARY KEY (id),
                UNIQUE (run_id),
                CHECK (
                    {_RFD_CHECK}
                ),
                FOREIGN KEY(run_id) REFERENCES runs (id),
                FOREIGN KEY(source_agent_execution_id) REFERENCES agent_executions (id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            CREATE INDEX ix_run_final_decisions_source_agent_execution_id
            ON run_final_decisions (source_agent_execution_id)
            """
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX ix_run_final_decisions_run_id ON run_final_decisions (run_id)"
        )
    )

    conn.execute(
        sa.text(
            """
            INSERT INTO run_final_decisions (
                id,
                run_id,
                source_agent_execution_id,
                decision_type,
                decision_date,
                is_existing_position,
                rating,
                recommended_action,
                conviction,
                rejection_reason,
                current_price,
                bear_intrinsic_value,
                base_intrinsic_value,
                bull_intrinsic_value,
                margin_of_safety_base_pct,
                margin_of_safety_verdict,
                primary_driver,
                red_flag_disposition,
                data_gap_disposition,
                thesis_expiry_note
            )
            SELECT
                id,
                run_id,
                source_agent_execution_id,
                CASE
                    WHEN decision_type = 'arbiter' THEN 'rating_table'
                    ELSE decision_type
                END,
                decision_date,
                is_existing_position,
                rating,
                recommended_action,
                conviction,
                rejection_reason,
                current_price,
                bear_intrinsic_value,
                base_intrinsic_value,
                bull_intrinsic_value,
                margin_of_safety_base_pct,
                margin_of_safety_verdict,
                primary_driver,
                red_flag_disposition,
                data_gap_disposition,
                thesis_expiry_note
            FROM _rfd_backup
            """
        )
    )

    conn.execute(
        sa.text(
            """
            CREATE TABLE run_final_decision_supporting_factors (
                id VARCHAR NOT NULL,
                run_final_decision_id VARCHAR NOT NULL,
                sort_order INTEGER NOT NULL,
                factor_text VARCHAR NOT NULL,
                PRIMARY KEY (id),
                UNIQUE (run_final_decision_id, sort_order),
                FOREIGN KEY(run_final_decision_id) REFERENCES run_final_decisions (id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            CREATE INDEX ix_run_final_decision_supporting_factors_run_final_decision_id
            ON run_final_decision_supporting_factors (run_final_decision_id)
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO run_final_decision_supporting_factors
            SELECT * FROM _rfdsf_backup
            """
        )
    )

    conn.execute(
        sa.text(
            """
            CREATE TABLE run_final_decision_mitigating_factors (
                id VARCHAR NOT NULL,
                run_final_decision_id VARCHAR NOT NULL,
                sort_order INTEGER NOT NULL,
                factor_text VARCHAR NOT NULL,
                PRIMARY KEY (id),
                UNIQUE (run_final_decision_id, sort_order),
                FOREIGN KEY(run_final_decision_id) REFERENCES run_final_decisions (id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            CREATE INDEX ix_run_final_decision_mitigating_factors_run_final_decision_id
            ON run_final_decision_mitigating_factors (run_final_decision_id)
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO run_final_decision_mitigating_factors
            SELECT * FROM _rfdmf_backup
            """
        )
    )

    conn.execute(sa.text("DROP TABLE _rfd_backup"))
    conn.execute(sa.text("DROP TABLE _rfdsf_backup"))
    conn.execute(sa.text("DROP TABLE _rfdmf_backup"))

    conn.execute(sa.text("PRAGMA foreign_keys=ON"))


def downgrade() -> None:
    raise NotImplementedError("Irreversible data migration (arbiter rows removed).")
