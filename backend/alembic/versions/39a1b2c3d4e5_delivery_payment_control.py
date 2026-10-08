"""add courier presence, delivery payment proofs and online cash payments"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "39a1b2c3d4e5"
down_revision = "38b1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "cash_payments",
        "session_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.add_column(
        "cash_payments",
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_cash_payments_order_id_orders",
        "cash_payments",
        "orders",
        ["order_id"],
        ["id"],
    )
    op.create_index(
        "uq_cash_payments_order_id",
        "cash_payments",
        ["order_id"],
        unique=True,
        postgresql_where=sa.text("order_id IS NOT NULL"),
    )

    op.create_table(
        "courier_presence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("courier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("online", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["courier_id"], ["users.id"]),
        sa.UniqueConstraint("courier_id", name="uq_courier_presence_courier"),
    )
    op.create_index("ix_courier_presence_courier_id", "courier_presence", ["courier_id"], unique=False)
    op.create_index("ix_courier_presence_last_seen", "courier_presence", ["last_seen"], unique=False)

    op.create_table(
        "delivery_payment_proofs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_method", sa.String(length=30), nullable=False, server_default="TRANSFER"),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("review_note", sa.String(length=255), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
    )
    op.create_index("ix_delivery_payment_proofs_order_id", "delivery_payment_proofs", ["order_id"], unique=False)
    op.create_index("ix_delivery_payment_proofs_status", "delivery_payment_proofs", ["status"], unique=False)
    op.create_index("ix_delivery_payment_proofs_created_at", "delivery_payment_proofs", ["created_at"], unique=False)


def downgrade():
    op.drop_index("ix_delivery_payment_proofs_created_at", table_name="delivery_payment_proofs")
    op.drop_index("ix_delivery_payment_proofs_status", table_name="delivery_payment_proofs")
    op.drop_index("ix_delivery_payment_proofs_order_id", table_name="delivery_payment_proofs")
    op.drop_table("delivery_payment_proofs")

    op.drop_index("ix_courier_presence_last_seen", table_name="courier_presence")
    op.drop_index("ix_courier_presence_courier_id", table_name="courier_presence")
    op.drop_table("courier_presence")

    op.drop_index("uq_cash_payments_order_id", table_name="cash_payments", postgresql_where=sa.text("order_id IS NOT NULL"))
    op.drop_constraint("fk_cash_payments_order_id_orders", "cash_payments", type_="foreignkey")
    op.drop_column("cash_payments", "order_id")
    op.alter_column(
        "cash_payments",
        "session_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
