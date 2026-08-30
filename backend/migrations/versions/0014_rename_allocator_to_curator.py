"""Rename persisted workflow-scoped Allocator executions to Curator.

Revision ID: 0014_rename_allocator_to_curator
Revises: 0013_portfolio_allocations
Create Date: 2026-08-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014_rename_allocator_to_curator"
down_revision = "0013_portfolio_allocations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE agent_executions SET agent_name = 'curator' "
            "WHERE agent_name = 'allocator'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE agent_executions SET agent_name = 'allocator' "
            "WHERE agent_name = 'curator'"
        )
    )
