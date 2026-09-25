"""create promotions and combos
Revision ID: 32c7d8e9f0a1
Revises: 31c6b3521b02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="32c7d8e9f0a1"
down_revision="31c6b3521b02"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("promotions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("promo_type", sa.String(20), nullable=False, server_default="PROMO"),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False))
def downgrade(): op.drop_table("promotions")
