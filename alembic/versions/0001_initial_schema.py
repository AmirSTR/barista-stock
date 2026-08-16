"""Initial database schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-16 06:30:00.000000

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
    # 1. Create bars table
    op.create_table(
        "bars",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("address", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bars")),
        sa.UniqueConstraint("code", name=op.f("uq_bars_code")),
    )
    op.create_index(op.f("ix_bars_code"), "bars", ["code"], unique=True)
    op.create_index(op.f("ix_bars_id"), "bars", ["id"], unique=False)

    # 2. Create products table
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("min_stock_alert", sa.Numeric(precision=12, scale=3), server_default="0", nullable=False),
        sa.Column("price", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
        sa.UniqueConstraint("sku", name=op.f("uq_products_sku")),
    )
    op.create_index(op.f("ix_products_category"), "products", ["category"], unique=False)
    op.create_index(op.f("ix_products_id"), "products", ["id"], unique=False)
    op.create_index(op.f("ix_products_name"), "products", ["name"], unique=False)
    op.create_index(op.f("ix_products_sku"), "products", ["sku"], unique=True)

    # 3. Create stocks table
    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bar_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("real_qty", sa.Numeric(precision=12, scale=3), server_default="0", nullable=False),
        sa.Column("reserved_qty", sa.Numeric(precision=12, scale=3), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("real_qty >= 0", name="ck_stock_real_qty_positive"),
        sa.CheckConstraint("reserved_qty >= 0", name="ck_stock_reserved_qty_positive"),
        sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], name=op.f("fk_stocks_bar_id_bars"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_stocks_product_id_products"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stocks")),
        sa.UniqueConstraint("bar_id", "product_id", name="uq_bar_product_stock"),
    )
    op.create_index(op.f("ix_stocks_bar_id"), "stocks", ["bar_id"], unique=False)
    op.create_index(op.f("ix_stocks_id"), "stocks", ["id"], unique=False)
    op.create_index(op.f("ix_stocks_product_id"), "stocks", ["product_id"], unique=False)

    # 4. Create orders table
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bar_id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.Enum("DRAFT", "PENDING", "APPROVED", "COMPLETED", "CANCELLED", name="orderstatus"), server_default="PENDING", nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], name=op.f("fk_orders_bar_id_bars"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_orders")),
    )
    op.create_index(op.f("ix_orders_bar_id"), "orders", ["bar_id"], unique=False)
    op.create_index(op.f("ix_orders_id"), "orders", ["id"], unique=False)
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)
    op.create_index(op.f("ix_orders_telegram_user_id"), "orders", ["telegram_user_id"], unique=False)

    # 5. Create order_items table
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_order_item_quantity_positive"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], name=op.f("fk_order_items_order_id_orders"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_order_items_product_id_products"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_items")),
    )
    op.create_index(op.f("ix_order_items_id"), "order_items", ["id"], unique=False)
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)
    op.create_index(op.f("ix_order_items_product_id"), "order_items", ["product_id"], unique=False)

    # 6. Create supplies table
    op.create_table(
        "supplies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bar_id", sa.Integer(), nullable=False),
        sa.Column("supplier_name", sa.String(length=255), nullable=True),
        sa.Column("invoice_photo_url", sa.String(length=1024), nullable=True),
        sa.Column("ocr_raw_text", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("DRAFT", "CONFIRMED", "CANCELLED", name="supplystatus"), server_default="DRAFT", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], name=op.f("fk_supplies_bar_id_bars"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_supplies")),
    )
    op.create_index(op.f("ix_supplies_bar_id"), "supplies", ["bar_id"], unique=False)
    op.create_index(op.f("ix_supplies_id"), "supplies", ["id"], unique=False)
    op.create_index(op.f("ix_supplies_status"), "supplies", ["status"], unique=False)

    # 7. Create supply_items table
    op.create_table(
        "supply_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("supply_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("raw_name", sa.String(length=255), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
        sa.Column("is_uncertain", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_supply_item_quantity_positive"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_supply_items_product_id_products"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["supply_id"], ["supplies.id"], name=op.f("fk_supply_items_supply_id_supplies"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_supply_items")),
    )
    op.create_index(op.f("ix_supply_items_id"), "supply_items", ["id"], unique=False)
    op.create_index(op.f("ix_supply_items_product_id"), "supply_items", ["product_id"], unique=False)
    op.create_index(op.f("ix_supply_items_supply_id"), "supply_items", ["supply_id"], unique=False)


def downgrade() -> None:
    op.drop_table("supply_items")
    op.drop_table("supplies")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("stocks")
    op.drop_table("products")
    op.drop_table("bars")
    op.execute("DROP TYPE IF EXISTS supplystatus")
    op.execute("DROP TYPE IF EXISTS orderstatus")
