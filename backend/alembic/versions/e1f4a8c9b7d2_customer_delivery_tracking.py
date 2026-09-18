"""add customer delivery tracking fields"""
from alembic import op
import sqlalchemy as sa

revision = "e1f4a8c9b7d2"
down_revision = "d9e7f1c2b3a4"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("orders", sa.Column("notes", sa.String(length=300), nullable=True))
    op.add_column("orders", sa.Column("delivery_address", sa.String(length=300), nullable=True))
    op.add_column("orders", sa.Column("delivery_phone", sa.String(length=30), nullable=True))
    op.add_column("orders", sa.Column("cashier_confirmed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_column("orders", "dispatched_at")
    op.drop_column("orders", "cashier_confirmed_at")
    op.drop_column("orders", "delivery_phone")
    op.drop_column("orders", "delivery_address")
    op.drop_column("orders", "notes")
