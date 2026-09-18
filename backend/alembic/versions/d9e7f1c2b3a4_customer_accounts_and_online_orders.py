"""customer consent and online orders

Revision ID: d9e7f1c2b3a4
Revises: c8cashier2026
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d9e7f1c2b3a4"
down_revision: Union[str, Sequence[str], None] = "c8cashier2026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================
    # USERS: TÉRMINOS Y CONDICIONES
    # ==========================================================

    op.add_column("users", sa.Column("terms_accepted", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("terms_version", sa.String(length=30), nullable=True))

    # ==========================================================
    # USERS: MARKETING / PUBLICIDAD
    # ==========================================================

    op.add_column("users", sa.Column("marketing_opt_in", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("marketing_consent_at", sa.DateTime(timezone=True), nullable=True))

    # ==========================================================
    # ORDERS: CLIENTE Y TIPO DE PEDIDO
    # ==========================================================

    op.add_column("orders", sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("orders", sa.Column("order_type", sa.String(length=30), nullable=False, server_default="TABLE"))
    op.alter_column("orders", "session_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)

    op.create_index("ix_orders_customer_id", "orders", ["customer_id"], unique=False)
    op.create_foreign_key("fk_orders_customer_id_users", "orders", "users", ["customer_id"], ["id"])


def downgrade() -> None:
    # ==========================================================
    # ORDERS: REVERTIR CAMBIOS
    # ==========================================================

    op.drop_constraint("fk_orders_customer_id_users", "orders", type_="foreignkey")
    op.drop_index("ix_orders_customer_id", table_name="orders")
    op.alter_column("orders", "session_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.drop_column("orders", "order_type")
    op.drop_column("orders", "customer_id")

    # ==========================================================
    # USERS: REVERTIR CAMBIOS
    # ==========================================================

    op.drop_column("users", "marketing_consent_at")
    op.drop_column("users", "marketing_opt_in")
    op.drop_column("users", "terms_version")
    op.drop_column("users", "terms_accepted_at")
    op.drop_column("users", "terms_accepted")