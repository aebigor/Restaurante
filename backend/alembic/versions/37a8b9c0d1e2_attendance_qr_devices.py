"""add QR attendance, schedules and authorized devices

Revision ID: 37a8b9c0d1e2
Revises: 36a1b2c3d4e5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "37a8b9c0d1e2"
down_revision = "36a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "attendance_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("qr_token", sa.String(length=80), nullable=False),
        sa.Column("pin_hash", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("qr_token"),
    )
    op.create_index("ix_attendance_profiles_user_id", "attendance_profiles", ["user_id"], unique=True)
    op.create_index("ix_attendance_profiles_qr_token", "attendance_profiles", ["qr_token"], unique=True)

    op.create_table(
        "attendance_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("tolerance_minutes", sa.Integer(), nullable=False, server_default="5"),
        sa.ForeignKeyConstraint(["profile_id"], ["attendance_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "weekday", name="uq_attendance_schedule_profile_weekday"),
    )
    op.create_index("ix_attendance_schedules_profile_id", "attendance_schedules", ["profile_id"], unique=False)

    op.create_table(
        "attendance_devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_uuid", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("pairing_code", sa.String(length=10), nullable=True),
        sa.Column("pairing_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_token_hash", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_uuid"),
        sa.UniqueConstraint("device_token_hash"),
    )
    op.create_index("ix_attendance_devices_device_uuid", "attendance_devices", ["device_uuid"], unique=True)
    op.create_index("ix_attendance_devices_pairing_code", "attendance_devices", ["pairing_code"], unique=False)
    op.create_index("ix_attendance_devices_status", "attendance_devices", ["status"], unique=False)

    op.create_table(
        "attendance_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("work_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entry_status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("exit_status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("late_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("early_leave_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overtime_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("adjustment_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("adjustment_reason", sa.Text(), nullable=True),
        sa.Column("adjusted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["device_id"], ["attendance_devices.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["adjusted_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attendance_records_user_id", "attendance_records", ["user_id"], unique=False)
    op.create_index("ix_attendance_records_device_id", "attendance_records", ["device_id"], unique=False)
    op.create_index("ix_attendance_records_work_date", "attendance_records", ["work_date"], unique=False)


def downgrade():
    op.drop_index("ix_attendance_records_work_date", table_name="attendance_records")
    op.drop_index("ix_attendance_records_device_id", table_name="attendance_records")
    op.drop_index("ix_attendance_records_user_id", table_name="attendance_records")
    op.drop_table("attendance_records")
    op.drop_index("ix_attendance_devices_status", table_name="attendance_devices")
    op.drop_index("ix_attendance_devices_pairing_code", table_name="attendance_devices")
    op.drop_index("ix_attendance_devices_device_uuid", table_name="attendance_devices")
    op.drop_table("attendance_devices")
    op.drop_index("ix_attendance_schedules_profile_id", table_name="attendance_schedules")
    op.drop_table("attendance_schedules")
    op.drop_index("ix_attendance_profiles_qr_token", table_name="attendance_profiles")
    op.drop_index("ix_attendance_profiles_user_id", table_name="attendance_profiles")
    op.drop_table("attendance_profiles")
