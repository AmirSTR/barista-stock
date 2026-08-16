"""Database schema verification and auto-repair utilities.

Ensures all tables, required columns, and schema constraints exist and are compatible,
even if previous migrations or partial schema creations occurred.
"""

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models.base import Base
from app.models.bar import Bar
from app.models.product import Product
from app.models.stock import Stock
from app.models.order import Order, OrderItem
from app.models.supply import SupplyInvoice, SupplyItem


def _sync_ensure_schema(sync_conn) -> None:
    """Synchronously verify and repair database schema."""
    # 1. Ensure all model tables exist
    Base.metadata.create_all(sync_conn)

    inspector = inspect(sync_conn)
    tables = inspector.get_table_names()
    dialect_name = sync_conn.dialect.name

    # 2. Expand alembic_version version_num if it exists
    if "alembic_version" in tables and dialect_name == "postgresql":
        try:
            sync_conn.execute(sa.text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)"))
        except Exception:
            pass

    # 3. Model definitions lookup
    model_tables = {
        "bars": Bar,
        "products": Product,
        "stocks": Stock,
        "orders": Order,
        "order_items": OrderItem,
        "supply_invoices": SupplyInvoice,
        "supply_items": SupplyItem,
    }

    # 4. For every table, drop NOT NULL on any legacy columns not present in our SQLAlchemy model
    if dialect_name == "postgresql":
        for table_name, model_cls in model_tables.items():
            if table_name in tables:
                expected_cols = {col.name for col in model_cls.__table__.columns}
                db_cols = inspector.get_columns(table_name)
                for col in db_cols:
                    col_name = col["name"]
                    # If the column is in DB but not in our model and is NOT NULL, drop NOT NULL constraint
                    if col_name not in expected_cols and not col.get("nullable", True):
                        try:
                            sync_conn.execute(sa.text(f'ALTER TABLE "{table_name}" ALTER COLUMN "{col_name}" DROP NOT NULL'))
                        except Exception:
                            pass

    # 5. Check 'bars' table for 'telegram_chat_id'
    if "bars" in tables:
        columns = [c["name"] for c in inspector.get_columns("bars")]
        if "telegram_chat_id" not in columns:
            col_type = "BIGINT" if dialect_name == "postgresql" else "INTEGER"
            sync_conn.execute(sa.text(f"ALTER TABLE bars ADD COLUMN telegram_chat_id {col_type}"))
            try:
                sync_conn.execute(
                    sa.text("CREATE INDEX IF NOT EXISTS ix_bars_telegram_chat_id ON bars (telegram_chat_id)")
                )
            except Exception:
                pass

    # 6. Check 'supply_invoices' table for 'invoice_number'
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
