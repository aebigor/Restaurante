"""add cash register movements

Revision ID: 35f0c1d2e3a4
Revises: 34e9f0a1b2c3
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "35f0c1d2e3a4"
down_revision = "34e9f0a1b2c3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cash_register_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cash_register_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cashier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movement_type", sa.String(length=30), nullable=False, server_default="WITHDRAWAL"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("recipient_name", sa.String(length=150), nullable=False),
        sa.Column("recipient_document", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cash_register_id"], ["cash_registers.id"]),
        sa.ForeignKeyConstraint(["cashier_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cash_register_movements_cash_register_id",
        "cash_register_movements",
        ["cash_register_id"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_cash_register_movements_cash_register_id", table_name="cash_register_movements")
    op.drop_table("cash_register_movements")
