"""add table payment mode and comanda print priority

Revision ID: 33d8e9f0a1b2
Revises: 32c7d8e9f0a1
"""
from alembic import op
import sqlalchemy as sa

revision = "33d8e9f0a1b2"
down_revision = "32c7d8e9f0a1"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("tables")}

    if "prepayment_required" not in cols:
        op.add_column(
            "tables",
            sa.Column(
                "prepayment_required",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )

    if "comanda_print_priority" not in cols:
        op.add_column(
            "tables",
            sa.Column(
                "comanda_print_priority",
                sa.Integer(),
                nullable=False,
                server_default="2",
            ),
        )


def downgrade():
    op.drop_column("tables", "comanda_print_priority")
    op.drop_column("tables", "prepayment_required")
