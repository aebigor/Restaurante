"""create cashier module"""

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql


revision = "c8cashier2026"

down_revision = (
    "7d94dafe57f3",
    "ab12cd34ef56"
)

branch_labels = None

depends_on = None


def upgrade():

    op.create_table(

        "cash_registers",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),

        sa.Column(
            "opened_by",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),

        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False
        ),

        sa.Column(
            "opening_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0"
        ),

        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="OPEN"
        ),

        sa.Column(
            "closed_at",
            sa.DateTime(timezone=True),
            nullable=True
        ),

        sa.Column(
            "closing_amount",
            sa.Numeric(12, 2),
            nullable=True
        ),

        sa.Column(
            "expected_cash",
            sa.Numeric(12, 2),
            nullable=True
        ),

        sa.Column(
            "difference",
            sa.Numeric(12, 2),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ["opened_by"],
            ["users.id"]
        ),

        sa.PrimaryKeyConstraint("id")

    )


    op.create_table(

        "cash_payments",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),

        sa.Column(
            "cash_register_id",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),

        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),

        sa.Column(
            "cashier_id",
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),

        sa.Column(
            "method",
            sa.String(30),
            nullable=False
        ),

        sa.Column(
            "amount",
            sa.Numeric(12, 2),
            nullable=False
        ),

        sa.Column(
            "received_amount",
            sa.Numeric(12, 2),
            nullable=False
        ),

        sa.Column(
            "change_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0"
        ),

        sa.Column(
            "reference",
            sa.String(150),
            nullable=True
        ),

        sa.Column(
            "paid_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ["cash_register_id"],
            ["cash_registers.id"]
        ),

        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"]
        ),

        sa.ForeignKeyConstraint(
            ["cashier_id"],
            ["users.id"]
        ),

        sa.PrimaryKeyConstraint("id")

    )


def downgrade():

    op.drop_table(
        "cash_payments"
    )

    op.drop_table(
        "cash_registers"
    )