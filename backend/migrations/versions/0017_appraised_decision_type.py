"""Add ``appraised`` decision type; allow null ratings; drop allocation policy CHECK.

Revision ID: 0017_appraised_decision_type
Revises: 0016_workflow_sterling_ledger
Create Date: 2026-09-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0017_appraised_decision_type"
down_revision = "0016_workflow_sterling_ledger"
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
OR
(
    decision_type = 'data_quality_rejection'
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
OR
(
    decision_type = 'appraised'
    AND rating IS NULL
    AND recommended_action IS NULL
    AND rejection_reason IS NULL
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
                decision_type VARCHAR(22) NOT NULL,
                decision_date DATE NOT NULL,
                is_existing_position BOOLEAN NOT NULL,
                rating VARCHAR,
                recommended_action VARCHAR,
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

    with op.batch_alter_table("portfolio_allocation_positions") as batch_op:
        batch_op.drop_constraint("portfolio_allocation_position_policy", type_="check")
        batch_op.alter_column(
            "policy_kind",
            existing_type=sa.String(),
            nullable=True,
        )


def downgrade() -> None:
    raise NotImplementedError("Irreversible schema widening for appraised decisions.")
