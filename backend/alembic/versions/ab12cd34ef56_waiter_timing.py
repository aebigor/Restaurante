"""add served_at to orders for waiter timing

Revision ID: ab12cd34ef56
Revises: 9a3f6b2c1d44
"""
from alembic import op
import sqlalchemy as sa

revision = "ab12cd34ef56"
down_revision = "9a3f6b2c1d44"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("orders")}
    if "served_at" not in cols:
        op.add_column(
            "orders",
            sa.Column("served_at", sa.DateTime(timezone=True), nullable=True)
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("orders")}
    if "served_at" in cols:
        op.drop_column("orders", "served_at")
