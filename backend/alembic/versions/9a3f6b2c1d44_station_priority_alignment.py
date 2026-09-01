"""align stations with the existing restaurant schema

Revision ID: 9a3f6b2c1d44
Revises: 8d8b8f2a1c90
"""
from alembic import op
import sqlalchemy as sa

revision = "9a3f6b2c1d44"
down_revision = "8d8b8f2a1c90"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("stations")}

    # The original schema already defines priority as NOT NULL. This migration
    # only fills it for legacy rows and makes the default explicit.
    if "priority" in cols:
        op.execute("UPDATE stations SET priority = 1 WHERE priority IS NULL")
        op.alter_column("stations", "priority", server_default="1")
    else:
        op.add_column("stations", sa.Column("priority", sa.Integer(), nullable=True))
        op.execute("UPDATE stations SET priority = 1 WHERE priority IS NULL")
        op.alter_column("stations", "priority", nullable=False, server_default="1")

    expected = {
        "description": sa.Column("description", sa.String(200), nullable=True),
        "auto_print": sa.Column("auto_print", sa.Boolean(), nullable=False, server_default=sa.false()),
        "sound_notification": sa.Column("sound_notification", sa.Boolean(), nullable=False, server_default=sa.true()),
        "accepts_delivery": sa.Column("accepts_delivery", sa.Boolean(), nullable=False, server_default=sa.true()),
        "supports_queue": sa.Column("supports_queue", sa.Boolean(), nullable=False, server_default=sa.true()),
    }
    for name, column in expected.items():
        if name not in cols:
            op.add_column("stations", column)


def downgrade():
    pass
