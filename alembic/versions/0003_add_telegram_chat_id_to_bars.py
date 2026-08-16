"""Add telegram_chat_id to bars if not exists

Revision ID: 0003_add_telegram_chat_id_to_bars
Revises: 0002_add_invoice_number
Create Date: 2026-08-16 14:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "0003_add_telegram_chat_id_to_bars"
down_revision: Union[str, None] = "0002_add_invoice_number"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    
    if "bars" in tables:
        columns = [c["name"] for c in inspector.get_columns("bars")]
        if "telegram_chat_id" not in columns:
            op.add_column(
                "bars",
                sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True),
            )
            indexes = [idx["name"] for idx in inspector.get_indexes("bars")]
            if "ix_bars_telegram_chat_id" not in indexes:
                op.create_index(
                    op.f("ix_bars_telegram_chat_id"),
                    "bars",
                    ["telegram_chat_id"],
                    unique=False,
                )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    
    if "bars" in tables:
        columns = [c["name"] for c in inspector.get_columns("bars")]
        if "telegram_chat_id" in columns:
            indexes = [idx["name"] for idx in inspector.get_indexes("bars")]
            if "ix_bars_telegram_chat_id" in indexes:
                op.drop_index(op.f("ix_bars_telegram_chat_id"), table_name="bars")
            op.drop_column("bars", "telegram_chat_id")
