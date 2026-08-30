"""Add workflow-scoped investment thesis snapshot tables.

Revision ID: 0015_workflow_investment_theses
Revises: 0014_rename_allocator_to_curator
Create Date: 2026-08-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0015_workflow_investment_theses"
down_revision = "0014_rename_allocator_to_curator"
branch_labels = None
depends_on = None

_ORIGIN_CHECK = "origin IN ('replaced', 'copied_prior')"


def upgrade() -> None:
    op.create_table(
        "workflow_investment_theses",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workflow_run_id", sa.String(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("mispricing_type", sa.String(), nullable=False),
        sa.Column("market_belief", sa.String(), nullable=False),
        sa.Column("mispricing_argument", sa.String(), nullable=False),
        sa.Column("resolution_mechanism", sa.String(), nullable=False),
        sa.Column("conviction_level", sa.String(), nullable=False),
        sa.Column("origin", sa.String(), nullable=False),
        sa.CheckConstraint(_ORIGIN_CHECK, name="workflow_investment_thesis_origin"),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_run_id", "ticker"),
    )
    op.create_index(
        "ix_workflow_investment_theses_workflow_run_id",
        "workflow_investment_theses",
        ["workflow_run_id"],
    )
    op.create_table(
        "workflow_investment_thesis_falsification_conditions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workflow_investment_thesis_id", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("condition_text", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workflow_investment_thesis_id"], ["workflow_investment_theses.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_investment_thesis_id", "sort_order"),
    )
    op.create_index(
        "ix_workflow_investment_thesis_falsification_conditions_workflow_investment_thesis_id",
        "workflow_investment_thesis_falsification_conditions",
        ["workflow_investment_thesis_id"],
    )
    op.create_table(
        "workflow_investment_thesis_risks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workflow_investment_thesis_id", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("risk_text", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workflow_investment_thesis_id"], ["workflow_investment_theses.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_investment_thesis_id", "sort_order"),
    )
    op.create_index(
        "ix_workflow_investment_thesis_risks_workflow_investment_thesis_id",
        "workflow_investment_thesis_risks",
        ["workflow_investment_thesis_id"],
    )
    op.create_table(
        "workflow_investment_thesis_evaluation_questions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workflow_investment_thesis_id", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workflow_investment_thesis_id"], ["workflow_investment_theses.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_investment_thesis_id", "sort_order"),
    )
    op.create_index(
        "ix_workflow_investment_thesis_evaluation_questions_workflow_investment_thesis_id",
        "workflow_investment_thesis_evaluation_questions",
        ["workflow_investment_thesis_id"],
    )
    op.create_table(
        "workflow_investment_thesis_permanent_loss_scenarios",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workflow_investment_thesis_id", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("scenario_text", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workflow_investment_thesis_id"], ["workflow_investment_theses.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_investment_thesis_id", "sort_order"),
    )
    op.create_index(
        "ix_workflow_investment_thesis_permanent_loss_scenarios_workflow_investment_thesis_id",
        "workflow_investment_thesis_permanent_loss_scenarios",
        ["workflow_investment_thesis_id"],
    )
    with op.batch_alter_table("mispricing_theses") as batch_op:
        batch_op.add_column(
            sa.Column(
                "origin",
                sa.String(),
                nullable=False,
                server_default="replaced",
            )
        )
        batch_op.create_check_constraint(
            "mispricing_thesis_origin",
            _ORIGIN_CHECK,
        )


def downgrade() -> None:
    with op.batch_alter_table("mispricing_theses") as batch_op:
        batch_op.drop_constraint("mispricing_thesis_origin", type_="check")
        batch_op.drop_column("origin")
    op.drop_table("workflow_investment_thesis_permanent_loss_scenarios")
    op.drop_table("workflow_investment_thesis_evaluation_questions")
    op.drop_table("workflow_investment_thesis_risks")
    op.drop_table("workflow_investment_thesis_falsification_conditions")
    op.drop_table("workflow_investment_theses")
