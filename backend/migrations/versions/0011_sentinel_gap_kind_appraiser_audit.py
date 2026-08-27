"""Add Sentinel gap_kind and Appraiser share-count audit columns.

Revision ID: 0011_sentinel_gap_kind_appraiser_audit
Revises: 0010_unify_agent_executions
Create Date: 2026-08-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_sentinel_gap_kind_appraiser_audit"
down_revision = "0010_unify_agent_executions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "evaluation_question_assessments",
        sa.Column("gap_kind", sa.String(), nullable=False, server_default="none"),
    )
    op.add_column(
        "appraiser_reports",
        sa.Column("shares_outstanding", sa.Float(), nullable=True),
    )
    op.add_column(
        "appraiser_reports",
        sa.Column("share_count_source", sa.String(), nullable=True),
    )
    op.add_column(
        "appraiser_reports",
        sa.Column("quoted_price_unit", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("appraiser_reports", "quoted_price_unit")
    op.drop_column("appraiser_reports", "share_count_source")
    op.drop_column("appraiser_reports", "shares_outstanding")
    op.drop_column("evaluation_question_assessments", "gap_kind")
