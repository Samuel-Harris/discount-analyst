"""allow unknown conversation message parts

Revision ID: 0002_allow_unknown_conversation_message_parts
Revises: 0001_initial_dashboard_schema
Create Date: 2026-04-25 22:33:00.123559

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_allow_unknown_conversation_message_parts"
down_revision = "0001_initial_dashboard_schema"
branch_labels = None
depends_on = None

_TABLE = "agent_conversation_message_parts"
_INDEX = "ix_agent_conversation_message_parts_conversation_message_id"


def _create_parts_table_sql(*, allowed_text_kinds: str, table_name: str) -> str:
    return f"""
    CREATE TABLE {table_name} (
        id VARCHAR NOT NULL,
        conversation_message_id VARCHAR NOT NULL,
        part_index INTEGER NOT NULL,
        part_kind VARCHAR(13) NOT NULL,
        content_text VARCHAR,
        tool_name VARCHAR,
        tool_call_id VARCHAR,
        PRIMARY KEY (id),
        UNIQUE (conversation_message_id, part_index),
        CHECK (
            (
                part_kind IN ({allowed_text_kinds})
                AND content_text IS NOT NULL
            )
            OR
            (
                part_kind = 'tool_call'
                AND tool_name IS NOT NULL
                AND tool_call_id IS NOT NULL
            )
            OR
            (
                part_kind = 'tool_return'
                AND content_text IS NOT NULL
                AND tool_name IS NOT NULL
                AND tool_call_id IS NOT NULL
            )
        ),
        FOREIGN KEY(conversation_message_id)
            REFERENCES agent_conversation_messages (id)
    )
    """


def _replace_parts_table(*, allowed_text_kinds: str, part_kind_expr: str) -> None:
    temp_table = f"{_TABLE}_new"
    op.execute(
        sa.text(
            _create_parts_table_sql(
                allowed_text_kinds=allowed_text_kinds, table_name=temp_table
            )
        )
    )
    op.execute(
        sa.text(
            f"""
            INSERT INTO {temp_table} (
                id,
                conversation_message_id,
                part_index,
                part_kind,
                content_text,
                tool_name,
                tool_call_id
            )
            SELECT
                id,
                conversation_message_id,
                part_index,
                {part_kind_expr},
                content_text,
                tool_name,
                tool_call_id
            FROM {_TABLE}
            """
        )
    )
    op.drop_index(_INDEX, table_name=_TABLE)
    op.drop_table(_TABLE)
    op.rename_table(temp_table, _TABLE)
    op.create_index(_INDEX, _TABLE, ["conversation_message_id"])


_OLD_TEXT_KINDS = "'system_prompt', 'user_prompt', 'text', 'retry_prompt'"
_NEW_TEXT_KINDS = f"{_OLD_TEXT_KINDS}, 'unknown'"


def upgrade() -> None:
    _replace_parts_table(
        allowed_text_kinds=_NEW_TEXT_KINDS,
        part_kind_expr="part_kind",
    )


def downgrade() -> None:
    _replace_parts_table(
        allowed_text_kinds=_OLD_TEXT_KINDS,
        part_kind_expr="CASE WHEN part_kind = 'unknown' THEN 'text' ELSE part_kind END",
    )
