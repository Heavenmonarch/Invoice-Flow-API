"""add commission model to org and product cost price

Revision ID: 9b6efef9a63f
Revises: dc46bb61831f
Create Date: 2026-09-05 20:21:52.232275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b6efef9a63f'
down_revision: Union[str, Sequence[str], None] = 'dc46bb61831f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1 — create the enum type in Postgres first
    op.execute("CREATE TYPE commissionmodel AS ENUM ('price_based', 'profit_based')")

    # Step 2 — add the column as nullable first
    op.add_column('organizations', sa.Column(
        'commission_model',
        sa.Enum('price_based', 'profit_based', name='commissionmodel'),
        nullable=True,
    ))

    # Step 3 — fill existing rows with the default value
    op.execute("UPDATE organizations SET commission_model = 'price_based'")

    # Step 4 — now make it non-nullable
    op.alter_column('organizations', 'commission_model', nullable=False)

    # Step 5 — add cost_price to products
    op.add_column('products', sa.Column('cost_price', sa.Numeric(12, 2), nullable=True))

    # Step 6 — add new columns to sales
    op.add_column('sales', sa.Column('cost_price', sa.Numeric(12, 2), nullable=True))
    op.add_column('sales', sa.Column('profit_amount', sa.Numeric(12, 2), nullable=True))
    op.add_column('sales', sa.Column('commission_model', sa.String(20), nullable=True))

    # Step 7 — fill existing sale rows
    op.execute("UPDATE sales SET commission_model = 'price_based'")

    # Step 8 — make commission_model on sales non-nullable
    op.alter_column('sales', 'commission_model', nullable=False)


def downgrade() -> None:
    op.drop_column('sales', 'commission_model')
    op.drop_column('sales', 'profit_amount')
    op.drop_column('sales', 'cost_price')
    op.drop_column('products', 'cost_price')
    op.drop_column('organizations', 'commission_model')
    op.execute("DROP TYPE commissionmodel")
