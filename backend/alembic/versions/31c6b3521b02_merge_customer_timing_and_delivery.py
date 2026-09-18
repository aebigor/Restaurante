"""merge customer timing and delivery

Revision ID: 31c6b3521b02
Revises: f2a6b8c9d0e1, f3b7c9d1e2a4
Create Date: 2026-09-18 07:36:16.924856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31c6b3521b02'
down_revision: Union[str, Sequence[str], None] = ('f2a6b8c9d0e1', 'f3b7c9d1e2a4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
