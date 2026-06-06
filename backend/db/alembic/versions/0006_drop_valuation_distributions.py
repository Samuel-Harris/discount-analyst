"""Drop duplicate valuation_distributions table (AppraiserReport is canonical).

Revision ID: 0006_drop_valuation_distributions
Revises: 0005_appraiser_valuation_distribution
Create Date: 2026-06-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006_drop_valuation_distributions"
down_revision = "0005_appraiser_valuation_distribution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS valuation_distributions"))


def downgrade() -> None:
    raise NotImplementedError("Irreversible drop of valuation_distributions table.")
