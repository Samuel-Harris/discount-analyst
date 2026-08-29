"""Store per-turn token usage on conversation response messages.

Revision ID: 0012_conversation_message_usage
Revises: 0011_sentinel_gap_kind_appraiser_audit
Create Date: 2026-08-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012_conversation_message_usage"
down_revision = "0011_sentinel_gap_kind_appraiser_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_conversation_messages",
        sa.Column("input_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "agent_conversation_messages",
        sa.Column("output_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "agent_conversation_messages",
        sa.Column("cache_write_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "agent_conversation_messages",
        sa.Column("cache_read_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "agent_conversation_messages",
        sa.Column("total_tokens", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agent_conversation_messages", "total_tokens")
    op.drop_column("agent_conversation_messages", "cache_read_tokens")
    op.drop_column("agent_conversation_messages", "cache_write_tokens")
    op.drop_column("agent_conversation_messages", "output_tokens")
    op.drop_column("agent_conversation_messages", "input_tokens")
