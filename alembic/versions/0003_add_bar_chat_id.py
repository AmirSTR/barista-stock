"""Add telegram_chat_id to bars and relax legacy columns

Revision ID: 0003_add_bar_chat_id
Revises: 0002_add_invoice_number
Create Date: 2026-08-16 14:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "0003_add_bar_chat_id"
down_revision: Union[str, None] = "0002_add_invoice_number"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    dialect_name = bind.dialect.name
    
    # 1. Expand alembic_version column if on PostgreSQL
    if "alembic_version" in tables and dialect_name == "postgresql":
        try:
            op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)")
        except Exception:
            pass

    # 2. Update bars table
    if "bars" in tables:
        cols_info = inspector.get_columns("bars")
        columns = [c["name"] for c in cols_info]
        
        # If legacy 'code' column exists with NOT NULL, drop the constraint
        for c in cols_info:
            if c["name"] not in ("id", "name", "is_active", "telegram_chat_id") and not c.get("nullable", True):
                if dialect_name == "postgresql":
                    try:
                        op.execute(f"ALTER TABLE bars ALTER COLUMN {c['name']} DROP NOT NULL")
                    except Exception:
                        pass

        # Add telegram_chat_id if missing
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
