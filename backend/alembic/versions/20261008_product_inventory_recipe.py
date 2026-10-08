"""associate products with inventory items as recipes

Revision ID: 20261008_recipe
Revises: 388950030896
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261008_recipe"
down_revision = "388950030896"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "product_inventory_recipes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("inventory_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity_per_sale", sa.Numeric(12, 3), nullable=False, server_default="1"),
    )
    op.create_index("ix_product_inventory_recipes_product_id", "product_inventory_recipes", ["product_id"])
    op.create_index("ix_product_inventory_recipes_inventory_item_id", "product_inventory_recipes", ["inventory_item_id"])
    op.create_unique_constraint("uq_product_inventory_recipe", "product_inventory_recipes", ["product_id", "inventory_item_id"])

def downgrade():
    op.drop_constraint("uq_product_inventory_recipe", "product_inventory_recipes", type_="unique")
    op.drop_index("ix_product_inventory_recipes_inventory_item_id", table_name="product_inventory_recipes")
    op.drop_index("ix_product_inventory_recipes_product_id", table_name="product_inventory_recipes")
    op.drop_table("product_inventory_recipes")
