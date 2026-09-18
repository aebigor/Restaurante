"""add customer order timing fields

Revision ID: f2a6b8c9d0e1
Revises: e1f4a8c9b7d2
"""
from alembic import op
import sqlalchemy as sa

revision = "f2a6b8c9d0e1"
down_revision = "e1f4a8c9b7d2"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("orders", sa.Column("kitchen_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("ready_at", sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_column("orders", "ready_at")
    op.drop_column("orders", "kitchen_started_at")
