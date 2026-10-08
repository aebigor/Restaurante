"""add persistent meal start timestamp to restaurant sessions

Revision ID: 20261008_session_meal
Revises: 20261008_recipe_merge
"""
from alembic import op
import sqlalchemy as sa

revision = "20261008_session_meal"
down_revision = "20261008_recipe_merge"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("sessions")}
    if "meal_started_at" not in cols:
        op.add_column("sessions", sa.Column("meal_started_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("sessions")}
    if "meal_started_at" in cols:
        op.drop_column("sessions", "meal_started_at")
