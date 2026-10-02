"""Record USD cost of each dashboard agent attempt, including retries.

Revision ID: 0019_agent_attempt_costs
Revises: 0018_quality_gates
Create Date: 2026-10-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0019_agent_attempt_costs"
down_revision = "0018_quality_gates"
branch_labels = None
depends_on = None

_OUTCOME_CHECK = "outcome IN ('successful', 'unsuccessful')"


def upgrade() -> None:
    op.create_table(
        "agent_attempt_costs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("agent_execution_id", sa.String(), nullable=False),
        sa.Column("outcome", sa.String(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(_OUTCOME_CHECK, name="agent_attempt_cost_outcome"),
        sa.ForeignKeyConstraint(["agent_execution_id"], ["agent_executions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_agent_attempt_costs_agent_execution_id",
        "agent_attempt_costs",
        ["agent_execution_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_attempt_costs_agent_execution_id",
        table_name="agent_attempt_costs",
    )
    op.drop_table("agent_attempt_costs")
