"""Add runs.lane_aborted for explicit gate/lane abort retry targeting.

Revision ID: 0009_run_lane_aborted
Revises: 0008_candidate_snapshot_gate_columns
Create Date: 2026-07-11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_run_lane_aborted"
down_revision = "0008_candidate_snapshot_gate_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "runs",
        sa.Column(
            "lane_aborted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("runs", "lane_aborted")
