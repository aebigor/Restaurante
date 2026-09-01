from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "7d94dafe57f3"

down_revision: Union[str, Sequence[str], None] = "9a3f6b2c1d44"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ======================================================
    # MENUS
    # ======================================================

    op.create_table(
        "menus",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),

        sa.Column(
            "title",
            sa.String(length=120),
            nullable=False
        ),

        sa.Column(
            "slug",
            sa.String(length=150),
            nullable=False
        ),

        sa.Column(
            "description",
            sa.String(length=300),
            nullable=True
        ),

        sa.Column(
            "cover_image",
            sa.String(length=255),
            nullable=True
        ),

        sa.Column(
            "display_order",
            sa.Integer(),
            nullable=False,
            server_default="1"
        ),

        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true")
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint("title"),

        sa.UniqueConstraint("slug")
    )


    # ======================================================
    # MENU ITEMS
    # ======================================================

    op.create_table(
        "menu_items",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),

        sa.Column(
            "menu_id",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),

        sa.Column(
            "dish_id",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),

        sa.Column(
            "display_order",
            sa.Integer(),
            nullable=False,
            server_default="1"
        ),

        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true")
        ),

        sa.ForeignKeyConstraint(
            ["menu_id"],
            ["menus.id"],
            ondelete="CASCADE"
        ),

        sa.ForeignKeyConstraint(
            ["dish_id"],
            ["dishes.id"],
            ondelete="CASCADE"
        ),

        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:

    op.drop_table("menu_items")

    op.drop_table("menus")