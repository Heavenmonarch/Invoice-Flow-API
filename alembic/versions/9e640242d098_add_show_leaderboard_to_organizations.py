"""add show leaderboard to organizations

Revision ID: 9e640242d098
Revises: 9b6efef9a63f
Create Date: 2026-09-05 21:01:30.203325

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e640242d098'
down_revision: Union[str, Sequence[str], None] = '9b6efef9a63f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1 — add as nullable first
    op.add_column('organizations', sa.Column(
        'show_leaderboard', sa.Boolean(), nullable=True
    ))

    # Step 2 — fill existing rows with the default value
    op.execute("UPDATE organizations SET show_leaderboard = TRUE")

    # Step 3 — now make it non-nullable
    op.alter_column('organizations', 'show_leaderboard', nullable=False)


def downgrade() -> None:
    op.drop_column('organizations', 'show_leaderboard')