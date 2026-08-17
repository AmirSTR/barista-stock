"""fix legacy schema

Revision ID: 0004_fix_legacy_schema
Revises: 0003_add_bar_chat_id
Create Date: 2026-08-17 09:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_fix_legacy_schema'
down_revision: Union[str, None] = '0003_add_bar_chat_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # orders
    op.alter_column('orders', 'status',
               existing_type=sa.String(length=9),
               type_=sa.String(length=20),
               existing_nullable=False,
               existing_server_default="pending")
    op.create_foreign_key('fk_orders_bar_id_bars', 'orders', 'bars', ['bar_id'], ['id'], ondelete='RESTRICT')

    # order_items
    op.alter_column('order_items', 'confirmed_qty',
               existing_type=sa.Float(),
               nullable=True)
    op.create_foreign_key('fk_order_items_product_id_products', 'order_items', 'products', ['product_id'], ['id'], ondelete='RESTRICT')

    # supply_invoices
    op.alter_column('supply_invoices', 'status',
               existing_type=sa.String(length=9),
               type_=sa.String(length=20),
               existing_nullable=False,
               existing_server_default="draft")

    # supply_items
    op.drop_column('supply_items', 'is_uncertain')
    op.create_foreign_key('fk_supply_items_product_id_products', 'supply_items', 'products', ['product_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_supply_items_product_id_products', 'supply_items', type_='foreignkey')
    op.add_column('supply_items', sa.Column('is_uncertain', sa.Boolean(), autoincrement=False, nullable=True))
    op.execute("UPDATE supply_items SET is_uncertain = false")
    op.alter_column('supply_items', 'is_uncertain', nullable=False)
    
    op.alter_column('supply_invoices', 'status',
               existing_type=sa.String(length=20),
               type_=sa.String(length=9),
               existing_nullable=False,
               existing_server_default="draft")
               
    op.drop_constraint('fk_order_items_product_id_products', 'order_items', type_='foreignkey')
    op.execute("UPDATE order_items SET confirmed_qty = 0.0 WHERE confirmed_qty IS NULL")
    op.alter_column('order_items', 'confirmed_qty',
               existing_type=sa.Float(),
               nullable=False)
               
    op.drop_constraint('fk_orders_bar_id_bars', 'orders', type_='foreignkey')
    op.alter_column('orders', 'status',
               existing_type=sa.String(length=20),
               type_=sa.String(length=9),
               existing_nullable=False,
               existing_server_default="pending")
