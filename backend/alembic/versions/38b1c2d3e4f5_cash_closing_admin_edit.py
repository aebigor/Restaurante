"""allow one same-day admin correction of cash closing amount

Revision ID: 38b1c2d3e4f5
Revises: 37a8b9c0d1e2
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "38b1c2d3e4f5"
down_revision = "37a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("cash_registers", sa.Column("closing_amount_edit_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("cash_registers", sa.Column("closing_amount_edited_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("cash_registers", sa.Column("closing_amount_edited_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("cash_registers", sa.Column("closing_amount_edit_reason", sa.String(length=255), nullable=True))
    op.create_foreign_key(
        "fk_cash_registers_closing_amount_edited_by_users",
        "cash_registers",
        "users",
        ["closing_amount_edited_by"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("fk_cash_registers_closing_amount_edited_by_users", "cash_registers", type_="foreignkey")
    op.drop_column("cash_registers", "closing_amount_edit_reason")
    op.drop_column("cash_registers", "closing_amount_edited_by")
    op.drop_column("cash_registers", "closing_amount_edited_at")
    op.drop_column("cash_registers", "closing_amount_edit_count")
