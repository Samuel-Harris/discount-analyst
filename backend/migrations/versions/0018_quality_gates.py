"""Add Appraiser scenarios and Strategist thesis direction.

Revision ID: 0018_quality_gates
Revises: 0017_appraised_decision_type
Create Date: 2026-09-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0018_quality_gates"
down_revision = "0017_appraised_decision_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "appraiser_reports",
        sa.Column("scenarios_json", sa.String(), nullable=True),
    )
    op.add_column(
        "mispricing_theses",
        sa.Column("thesis_direction", sa.String(), nullable=True),
    )
    op.add_column(
        "workflow_investment_theses",
        sa.Column("thesis_direction", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workflow_investment_theses", "thesis_direction")
    op.drop_column("mispricing_theses", "thesis_direction")
    op.drop_column("appraiser_reports", "scenarios_json")
