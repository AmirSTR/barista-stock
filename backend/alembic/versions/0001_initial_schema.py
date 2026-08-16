"""Initial database schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Bars table
    op.create_table(
        "bars",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bars_name"), "bars", ["name"], unique=False)
    op.create_index(op.f("ix_bars_telegram_chat_id"), "bars", ["telegram_chat_id"], unique=False)

    # 2. Products table
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sku", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_products_sku"), "products", ["sku"], unique=True)
    op.create_index(op.f("ix_products_name"), "products", ["name"], unique=False)
    op.create_index(op.f("ix_products_category"), "products", ["category"], unique=False)

    # 3. Stocks table
    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("real_qty", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reserved_qty", sa.Float(), nullable=False, server_default="0.0"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
    )
    op.create_index(op.f("ix_stocks_product_id"), "stocks", ["product_id"], unique=True)

    # 4. Orders table
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bar_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_bar_id"), "orders", ["bar_id"], unique=False)
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)

    # 5. Order Items table
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("requested_qty", sa.Float(), nullable=False),
        sa.Column("confirmed_qty", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)
    op.create_index(op.f("ix_order_items_product_id"), "order_items", ["product_id"], unique=False)

    # 6. Supply Invoices table
    op.create_table(
        "supply_invoices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("photo_file_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_supply_invoices_status"), "supply_invoices", ["status"], unique=False)

    # 7. Supply Items table
    op.create_table(
        "supply_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("detected_name", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["supply_invoices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_supply_items_invoice_id"), "supply_items", ["invoice_id"], unique=False)
    op.create_index(op.f("ix_supply_items_product_id"), "supply_items", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_table("supply_items")
    op.drop_table("supply_invoices")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("stocks")
    op.drop_table("products")
    op.drop_table("bars")
