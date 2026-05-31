"""Migrate Appraiser persistence from DCF assumptions to valuation distributions.

Revision ID: 0005_appraiser_valuation_distribution
Revises: 0004_rating_table_decision_type
Create Date: 2026-05-31
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_appraiser_valuation_distribution"
down_revision = "0004_rating_table_decision_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys=OFF"))

    conn.execute(sa.text("DROP TABLE IF EXISTS dcf_valuations"))
    conn.execute(sa.text("DROP TABLE IF EXISTS appraiser_reports"))

    conn.execute(
        sa.text(
            """
            CREATE TABLE appraiser_reports (
                id VARCHAR NOT NULL,
                agent_execution_id VARCHAR NOT NULL,
                ticker VARCHAR NOT NULL,
                company_name VARCHAR NOT NULL,
                valuation_date VARCHAR NOT NULL,
                summary VARCHAR NOT NULL,
                currency VARCHAR NOT NULL,
                current_share_price FLOAT NOT NULL,
                expected_intrinsic_value FLOAT NOT NULL,
                p10_intrinsic_value FLOAT NOT NULL,
                p25_intrinsic_value FLOAT NOT NULL,
                p50_intrinsic_value FLOAT NOT NULL,
                p75_intrinsic_value FLOAT NOT NULL,
                p90_intrinsic_value FLOAT NOT NULL,
                distribution_method VARCHAR NOT NULL,
                distribution_reasoning VARCHAR NOT NULL,
                methods_json VARCHAR NOT NULL,
                key_value_drivers_json VARCHAR NOT NULL,
                downside_risks_to_value_json VARCHAR NOT NULL,
                upside_drivers_to_value_json VARCHAR NOT NULL,
                data_quality VARCHAR NOT NULL,
                caveats_json VARCHAR NOT NULL,
                PRIMARY KEY (id),
                UNIQUE (agent_execution_id),
                FOREIGN KEY(agent_execution_id) REFERENCES agent_executions (id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX ix_appraiser_reports_agent_execution_id "
            "ON appraiser_reports (agent_execution_id)"
        )
    )

    conn.execute(
        sa.text(
            """
            CREATE TABLE valuation_distributions (
                id VARCHAR NOT NULL,
                run_id VARCHAR NOT NULL,
                appraiser_agent_execution_id VARCHAR NOT NULL,
                currency VARCHAR NOT NULL,
                current_share_price FLOAT NOT NULL,
                expected_intrinsic_value FLOAT NOT NULL,
                p10_intrinsic_value FLOAT NOT NULL,
                p25_intrinsic_value FLOAT NOT NULL,
                p50_intrinsic_value FLOAT NOT NULL,
                p75_intrinsic_value FLOAT NOT NULL,
                p90_intrinsic_value FLOAT NOT NULL,
                distribution_method VARCHAR NOT NULL,
                distribution_reasoning VARCHAR NOT NULL,
                PRIMARY KEY (id),
                UNIQUE (run_id),
                UNIQUE (appraiser_agent_execution_id),
                FOREIGN KEY(run_id) REFERENCES runs (id),
                FOREIGN KEY(appraiser_agent_execution_id) REFERENCES agent_executions (id)
            )
            """
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX ix_valuation_distributions_run_id "
            "ON valuation_distributions (run_id)"
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX ix_valuation_distributions_appraiser_agent_execution_id "
            "ON valuation_distributions (appraiser_agent_execution_id)"
        )
    )

    conn.execute(sa.text("PRAGMA foreign_keys=ON"))


def downgrade() -> None:
    raise NotImplementedError("Irreversible Appraiser contract migration.")
