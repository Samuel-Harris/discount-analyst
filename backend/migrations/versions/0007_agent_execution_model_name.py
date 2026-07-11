"""Add nullable model_name to agent execution tables; backfill existing rows.

Revision ID: 0007_agent_execution_model_name
Revises: 0006_drop_valuation_distributions
Create Date: 2026-06-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# Canonical value for ModelName.GPT_5_1 — kept literal to avoid Alembic import graph.
_BACKFILL_MODEL_NAME = "gpt-5.1"


revision = "0007_agent_execution_model_name"
down_revision = "0006_drop_valuation_distributions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_executions",
        sa.Column("model_name", sa.String(), nullable=True),
    )
    op.add_column(
        "workflow_agent_executions",
        sa.Column("model_name", sa.String(), nullable=True),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE agent_executions SET model_name = :model_name WHERE model_name IS NULL"
        ),
        {"model_name": _BACKFILL_MODEL_NAME},
    )
    conn.execute(
        sa.text(
            "UPDATE workflow_agent_executions SET model_name = :model_name "
            "WHERE model_name IS NULL"
        ),
        {"model_name": _BACKFILL_MODEL_NAME},
    )


def downgrade() -> None:
    op.drop_column("workflow_agent_executions", "model_name")
    op.drop_column("agent_executions", "model_name")
