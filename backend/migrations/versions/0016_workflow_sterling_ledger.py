"""Add sterling ledger columns on workflow runs and portfolio ticker rows.

Revision ID: 0016_workflow_sterling_ledger
Revises: 0015_workflow_investment_theses
Create Date: 2026-08-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0016_workflow_sterling_ledger"
down_revision = "0015_workflow_investment_theses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workflow_runs") as batch_op:
        batch_op.add_column(sa.Column("cash_gbp", sa.Numeric(18, 2), nullable=True))
    with op.batch_alter_table("workflow_run_portfolio_tickers") as batch_op:
        batch_op.add_column(sa.Column("value_gbp", sa.Numeric(18, 2), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("workflow_run_portfolio_tickers") as batch_op:
        batch_op.drop_column("value_gbp")
    with op.batch_alter_table("workflow_runs") as batch_op:
        batch_op.drop_column("cash_gbp")
