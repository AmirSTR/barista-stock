"""Database schema verification and auto-repair utilities.

Ensures all tables and required columns exist even if previous migrations
or partial schema creations occurred.
"""

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models.base import Base


def _sync_ensure_schema(sync_conn) -> None:
    """Synchronously verify and repair database schema."""
    # 1. Ensure all model tables exist
    Base.metadata.create_all(sync_conn)

    inspector = inspect(sync_conn)
    tables = inspector.get_table_names()
    dialect_name = sync_conn.dialect.name

    # 2. Check 'bars' table for 'telegram_chat_id'
    if "bars" in tables:
        columns = [c["name"] for c in inspector.get_columns("bars")]
        if "telegram_chat_id" not in columns:
            col_type = "BIGINT" if dialect_name == "postgresql" else "INTEGER"
            sync_conn.execute(sa.text(f"ALTER TABLE bars ADD COLUMN telegram_chat_id {col_type}"))
            try:
                if dialect_name == "postgresql":
                    sync_conn.execute(
                        sa.text("CREATE INDEX IF NOT EXISTS ix_bars_telegram_chat_id ON bars (telegram_chat_id)")
                    )
                else:
                    sync_conn.execute(
                        sa.text("CREATE INDEX IF NOT EXISTS ix_bars_telegram_chat_id ON bars (telegram_chat_id)")
                    )
            except Exception:
                pass

    # 3. Check 'supply_invoices' table for 'invoice_number'
    if "supply_invoices" in tables:
        columns = [c["name"] for c in inspector.get_columns("supply_invoices")]
        if "invoice_number" not in columns:
            sync_conn.execute(sa.text("ALTER TABLE supply_invoices ADD COLUMN invoice_number VARCHAR(100)"))


async def ensure_schema(bind_engine: AsyncEngine = None) -> None:
    """Async wrapper to ensure database schema and required columns exist."""
    from app.core.database import engine
    target_engine = bind_engine or engine
    async with target_engine.begin() as conn:
        await conn.run_sync(_sync_ensure_schema)
