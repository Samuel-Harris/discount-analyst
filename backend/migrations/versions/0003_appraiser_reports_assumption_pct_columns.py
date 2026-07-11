"""appraiser_reports: store assumption rates as percentage points; rename columns

Revision ID: 0003_appraiser_reports_assumption_pct_columns
Revises: 0002_allow_unknown_conversation_message_parts
Create Date: 2026-05-17

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_appraiser_reports_assumption_pct_columns"
down_revision = "0002_allow_unknown_conversation_message_parts"
branch_labels = None
depends_on = None

_TABLE = "appraiser_reports"

_RENAMES: tuple[tuple[str, str], ...] = (
    ("assumed_tax_rate", "assumed_tax_rate_pct"),
    (
        "assumed_forecast_period_annual_revenue_growth_rate",
        "assumed_forecast_period_annual_revenue_growth_rate_pct",
    ),
    (
        "assumed_perpetuity_cash_flow_growth_rate",
        "assumed_perpetuity_cash_flow_growth_rate_pct",
    ),
    ("assumed_ebit_margin", "assumed_ebit_margin_pct"),
    (
        "assumed_depreciation_and_amortization_rate",
        "assumed_depreciation_and_amortization_rate_pct",
    ),
    ("assumed_capex_rate", "assumed_capex_rate_pct"),
    (
        "assumed_change_in_working_capital_rate",
        "assumed_change_in_working_capital_rate_pct",
    ),
)


def upgrade() -> None:
    op.execute(
        sa.text(
            f"""
            UPDATE {_TABLE} SET
                assumed_tax_rate = assumed_tax_rate * 100,
                assumed_forecast_period_annual_revenue_growth_rate =
                    assumed_forecast_period_annual_revenue_growth_rate * 100,
                assumed_perpetuity_cash_flow_growth_rate =
                    assumed_perpetuity_cash_flow_growth_rate * 100,
                assumed_ebit_margin = assumed_ebit_margin * 100,
                assumed_depreciation_and_amortization_rate =
                    assumed_depreciation_and_amortization_rate * 100,
                assumed_capex_rate = assumed_capex_rate * 100,
                assumed_change_in_working_capital_rate =
                    assumed_change_in_working_capital_rate * 100
            """
        )
    )
    for old, new in _RENAMES:
        op.execute(sa.text(f'ALTER TABLE {_TABLE} RENAME COLUMN "{old}" TO "{new}"'))


def downgrade() -> None:
    for old, new in _RENAMES:
        op.execute(sa.text(f'ALTER TABLE {_TABLE} RENAME COLUMN "{new}" TO "{old}"'))
    op.execute(
        sa.text(
            f"""
            UPDATE {_TABLE} SET
                assumed_tax_rate = assumed_tax_rate / 100,
                assumed_forecast_period_annual_revenue_growth_rate =
                    assumed_forecast_period_annual_revenue_growth_rate / 100,
                assumed_perpetuity_cash_flow_growth_rate =
                    assumed_perpetuity_cash_flow_growth_rate / 100,
                assumed_ebit_margin = assumed_ebit_margin / 100,
                assumed_depreciation_and_amortization_rate =
                    assumed_depreciation_and_amortization_rate / 100,
                assumed_capex_rate = assumed_capex_rate / 100,
                assumed_change_in_working_capital_rate =
                    assumed_change_in_working_capital_rate / 100
            """
        )
    )
