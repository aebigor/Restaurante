"""merge competing migration heads

Revision ID: 388950030896
Revises: 39a1b2c3d4e5, 39c2d4e6f8a0
Create Date: 2026-10-04 16:56:20.252039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '388950030896'
down_revision: Union[str, Sequence[str], None] = ('39a1b2c3d4e5', '39c2d4e6f8a0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
