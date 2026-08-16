"""Add invoice_number to supplies

Revision ID: 0002_add_invoice_number
Revises: 0001_initial_schema
Create Date: 2026-08-16 07:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_add_invoice_number"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("supplies", sa.Column("invoice_number", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("supplies", "invoice_number")
