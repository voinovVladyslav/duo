"""add password_updated_at to user

Revision ID: 88c0a8ed2795
Revises: e21e130a4991
Create Date: 2026-05-24 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '88c0a8ed2795'
down_revision: Union[str, Sequence[str], None] = 'e21e130a4991'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'user',
        sa.Column(
            'password_updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('NOW()'),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user', 'password_updated_at')
