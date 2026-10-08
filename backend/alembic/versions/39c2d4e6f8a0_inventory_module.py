"""create restaurant inventory module

Revision ID: 39c2d4e6f8a0
Revises: 38b1c2d3e4f5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "39c2d4e6f8a0"
down_revision = "38b1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "inventory_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("sku", sa.String(80), nullable=True, unique=True),
        sa.Column("barcode", sa.String(80), nullable=True, unique=True),
        sa.Column("category", sa.String(80), nullable=False, server_default="General"),
        sa.Column("item_type", sa.String(40), nullable=False, server_default="INGREDIENTE"),
        sa.Column("brand", sa.String(100)),
        sa.Column("presentation", sa.String(100)),
        sa.Column("unit", sa.String(20), nullable=False, server_default="unidad"),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.Column("min_quantity", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.Column("max_quantity", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.Column("reorder_quantity", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("storage", sa.String(80)),
        sa.Column("location", sa.String(120)),
        sa.Column("lot", sa.String(100)),
        sa.Column("purchase_date", sa.Date()),
        sa.Column("opened_date", sa.Date()),
        sa.Column("expiry_date", sa.Date()),
        sa.Column("storage_temperature", sa.String(80)),
        sa.Column("supplier", sa.String(160)),
        sa.Column("allergen", sa.String(160)),
        sa.Column("notes", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_inventory_items_name", "inventory_items", ["name"])
    op.create_table(
        "inventory_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movement_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("reason", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_inventory_movements_item_id", "inventory_movements", ["item_id"])


def downgrade():
    op.drop_index("ix_inventory_movements_item_id", table_name="inventory_movements")
    op.drop_table("inventory_movements")
    op.drop_index("ix_inventory_items_name", table_name="inventory_items")
    op.drop_table("inventory_items")
