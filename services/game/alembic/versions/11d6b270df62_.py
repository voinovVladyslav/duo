"""Add new enum value

Revision ID: 11d6b270df62
Revises: 955d762b14f2
Create Date: 2026-06-16 19:32:46.126377

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '11d6b270df62'
down_revision: Union[str, Sequence[str], None] = '955d762b14f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE type ADD VALUE IF NOT EXISTS 'BATTLESHIPS'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres cannot drop a single enum value; no-op downgrade.
    pass
