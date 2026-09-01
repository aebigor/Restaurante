"""create stations and update products

Revision ID: c4d65860c4cd
Revises: b4b64a71b45a
Create Date: 2026-08-04 21:40:18.454559

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4d65860c4cd"

down_revision: Union[str, Sequence[str], None] = "b4b64a71b45a"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    """Upgrade schema."""


    # ==========================================
    # AGREGAR CAMPOS A PRODUCTS
    # ==========================================


    op.add_column(
        "products",
        sa.Column(
            "code",
            sa.String(length=50),
            nullable=True
        )
    )


    op.add_column(
        "products",
        sa.Column(
            "preparation_time",
            sa.Integer(),
            nullable=False,
            server_default="10"
        )
    )


    op.add_column(
        "products",
        sa.Column(
            "stock",
            sa.Integer(),
            nullable=False,
            server_default="0"
        )
    )


    op.add_column(
        "products",
        sa.Column(
            "category_id",
            sa.UUID(),
            nullable=True
        )
    )


    # ==========================================
    # UNIQUE CODE PRODUCTO
    # ==========================================


    op.create_unique_constraint(
        "uq_products_code",
        "products",
        ["code"]
    )


    # ==========================================
    # RELACION PRODUCTO - CATEGORIA
    # ==========================================


    op.create_foreign_key(
        "fk_products_category",
        "products",
        "categories",
        ["category_id"],
        ["id"]
    )



def downgrade() -> None:
    """Downgrade schema."""


    op.drop_constraint(
        "fk_products_category",
        "products",
        type_="foreignkey"
    )


    op.drop_constraint(
        "uq_products_code",
        "products",
        type_="unique"
    )


    op.drop_column(
        "products",
        "category_id"
    )


    op.drop_column(
        "products",
        "stock"
    )


    op.drop_column(
        "products",
        "preparation_time"
    )


    op.drop_column(
        "products",
        "code"
    )