"""Add normalised portfolio allocation tables and backfill Allocator executions.

Revision ID: 0013_portfolio_allocations
Revises: 0012_conversation_message_usage
Create Date: 2026-08-30
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op

revision = "0013_portfolio_allocations"
down_revision = "0012_conversation_message_usage"
branch_labels = None
depends_on = None

_LEGACY_SKIP_REASON = "legacy_workflow_without_position_snapshot"

_WEIGHT_RANGE_CHECK = (
    "0 <= acceptable_weight_low_pct "
    "AND acceptable_weight_low_pct <= target_weight_pct "
    "AND target_weight_pct <= acceptable_weight_high_pct "
    "AND acceptable_weight_high_pct <= 100 "
    "AND 0 <= current_weight_pct AND current_weight_pct <= 100"
)

_POLICY_CHECK = """
(
    policy_kind = 'investable'
    AND forced_zero_reason IS NULL
)
OR
(
    policy_kind = 'retain_or_reduce'
    AND forced_zero_reason IS NULL
    AND target_weight_pct <= current_weight_pct
    AND acceptable_weight_high_pct <= current_weight_pct
)
OR
(
    policy_kind = 'forced_zero'
    AND forced_zero_reason IS NOT NULL
    AND target_weight_pct = 0
    AND acceptable_weight_low_pct = 0
    AND acceptable_weight_high_pct = 0
)
"""

_CASH_RANGE_CHECK = (
    "0 <= cash_acceptable_weight_low_pct "
    "AND cash_acceptable_weight_low_pct <= cash_target_weight_pct "
    "AND cash_target_weight_pct <= cash_acceptable_weight_high_pct "
    "AND cash_acceptable_weight_high_pct <= 100 "
    "AND 0 <= current_cash_weight_pct AND current_cash_weight_pct <= 100"
)


def upgrade() -> None:
    op.create_table(
        "portfolio_allocations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("agent_execution_id", sa.String(), nullable=False),
        sa.Column("allocation_date", sa.Date(), nullable=False),
        sa.Column("current_cash_weight_pct", sa.Float(), nullable=False),
        sa.Column("cash_target_weight_pct", sa.Float(), nullable=False),
        sa.Column("cash_acceptable_weight_low_pct", sa.Float(), nullable=False),
        sa.Column("cash_acceptable_weight_high_pct", sa.Float(), nullable=False),
        sa.Column("cash_rationale", sa.String(), nullable=False),
        sa.Column("portfolio_rationale", sa.String(), nullable=False),
        sa.CheckConstraint(_CASH_RANGE_CHECK, name="portfolio_allocation_cash_range"),
        sa.ForeignKeyConstraint(["agent_execution_id"], ["agent_executions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_execution_id"),
    )
    op.create_index(
        "ix_portfolio_allocations_agent_execution_id",
        "portfolio_allocations",
        ["agent_execution_id"],
    )
    op.create_table(
        "portfolio_allocation_positions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("allocation_id", sa.String(), nullable=False),
        sa.Column("source_run_id", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("is_existing_position", sa.Boolean(), nullable=False),
        sa.Column("current_weight_pct", sa.Float(), nullable=False),
        sa.Column("policy_kind", sa.String(), nullable=False),
        sa.Column("forced_zero_reason", sa.String(), nullable=True),
        sa.Column("target_weight_pct", sa.Float(), nullable=False),
        sa.Column("acceptable_weight_low_pct", sa.Float(), nullable=False),
        sa.Column("acceptable_weight_high_pct", sa.Float(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("rationale", sa.String(), nullable=False),
        sa.CheckConstraint(
            _WEIGHT_RANGE_CHECK, name="portfolio_allocation_position_range"
        ),
        sa.CheckConstraint(_POLICY_CHECK, name="portfolio_allocation_position_policy"),
        sa.ForeignKeyConstraint(["allocation_id"], ["portfolio_allocations.id"]),
        sa.ForeignKeyConstraint(["source_run_id"], ["runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("allocation_id", "source_run_id"),
        sa.UniqueConstraint("allocation_id", "sort_order"),
    )
    op.create_index(
        "ix_portfolio_allocation_positions_allocation_id",
        "portfolio_allocation_positions",
        ["allocation_id"],
    )
    op.create_index(
        "ix_portfolio_allocation_positions_source_run_id",
        "portfolio_allocation_positions",
        ["source_run_id"],
    )
    op.create_table(
        "portfolio_allocation_risk_clusters",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("allocation_id", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("mechanism", sa.String(), nullable=False),
        sa.Column("allocation_effect", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["allocation_id"], ["portfolio_allocations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("allocation_id", "sort_order"),
        sa.UniqueConstraint("allocation_id", "label"),
    )
    op.create_index(
        "ix_portfolio_allocation_risk_clusters_allocation_id",
        "portfolio_allocation_risk_clusters",
        ["allocation_id"],
    )
    op.create_table(
        "portfolio_allocation_risk_cluster_members",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("cluster_id", sa.String(), nullable=False),
        sa.Column("allocation_position_id", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["cluster_id"], ["portfolio_allocation_risk_clusters.id"]
        ),
        sa.ForeignKeyConstraint(
            ["allocation_position_id"], ["portfolio_allocation_positions.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cluster_id", "allocation_position_id"),
        sa.UniqueConstraint("cluster_id", "sort_order"),
    )
    op.create_index(
        "ix_portfolio_allocation_risk_cluster_members_cluster_id",
        "portfolio_allocation_risk_cluster_members",
        ["cluster_id"],
    )
    op.create_index(
        "ix_portfolio_allocation_risk_cluster_members_allocation_position_id",
        "portfolio_allocation_risk_cluster_members",
        ["allocation_position_id"],
    )

    connection = op.get_bind()
    workflow_ids = connection.execute(
        sa.text("SELECT id FROM workflow_runs")
    ).fetchall()
    existing = {
        row[0]
        for row in connection.execute(
            sa.text(
                """
                SELECT workflow_run_id FROM agent_executions
                WHERE agent_name = 'allocator' AND workflow_run_id IS NOT NULL
                """
            )
        ).fetchall()
    }
    for (workflow_run_id,) in workflow_ids:
        if workflow_run_id in existing:
            continue
        connection.execute(
            sa.text(
                """
                INSERT INTO agent_executions (
                    id, workflow_run_id, run_id, agent_name, status,
                    started_at, completed_at, error_message, model_name
                )
                VALUES (
                    :id, :workflow_run_id, NULL, 'allocator', 'skipped',
                    NULL, NULL, :reason, NULL
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "workflow_run_id": workflow_run_id,
                "reason": _LEGACY_SKIP_REASON,
            },
        )


def downgrade() -> None:
    op.drop_table("portfolio_allocation_risk_cluster_members")
    op.drop_table("portfolio_allocation_risk_clusters")
    op.drop_table("portfolio_allocation_positions")
    op.drop_table("portfolio_allocations")
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            DELETE FROM agent_conversation_message_parts
            WHERE conversation_message_id IN (
                SELECT m.id
                FROM agent_conversation_messages AS m
                JOIN agent_conversations AS c ON c.id = m.conversation_id
                JOIN agent_executions AS e ON e.id = c.agent_execution_id
                WHERE e.agent_name = 'allocator'
            )
            """
        )
    )
    connection.execute(
        sa.text(
            """
            DELETE FROM agent_conversation_messages
            WHERE conversation_id IN (
                SELECT c.id
                FROM agent_conversations AS c
                JOIN agent_executions AS e ON e.id = c.agent_execution_id
                WHERE e.agent_name = 'allocator'
            )
            """
        )
    )
    connection.execute(
        sa.text(
            """
            DELETE FROM agent_conversations
            WHERE agent_execution_id IN (
                SELECT id FROM agent_executions WHERE agent_name = 'allocator'
            )
            """
        )
    )
    connection.execute(
        sa.text("DELETE FROM agent_executions WHERE agent_name = 'allocator'")
    )
