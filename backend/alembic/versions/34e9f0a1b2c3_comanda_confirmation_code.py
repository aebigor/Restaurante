"""add confirmation code to prepayment orders

Revision ID: 34e9f0a1b2c3
Revises: 33d8e9f0a1b2
"""
from alembic import op
import sqlalchemy as sa

revision = "34e9f0a1b2c3"
down_revision = "33d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("orders")}
    if "confirmation_code" not in cols:
        op.add_column("orders", sa.Column("confirmation_code", sa.String(length=6), nullable=True))
        op.create_index("ix_orders_confirmation_code", "orders", ["confirmation_code"], unique=False)


def downgrade():
    op.drop_index("ix_orders_confirmation_code", table_name="orders")
    op.drop_column("orders", "confirmation_code")
