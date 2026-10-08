"""Kitchen timing, queue close on waiter delivery and web push subscriptions."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="4a7b8c9d0e1f"; down_revision="388950030896"; branch_labels=None; depends_on=None
def upgrade():
 op.add_column("kitchen_queue",sa.Column("overdue_notified_at",sa.DateTime(),nullable=True))
 op.create_table("push_subscriptions",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("endpoint",sa.Text(),nullable=False),sa.Column("p256dh",sa.Text(),nullable=False),sa.Column("auth",sa.Text(),nullable=False),sa.Column("user_id",postgresql.UUID(as_uuid=True),nullable=True),sa.Column("station_id",postgresql.UUID(as_uuid=True),nullable=True),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),sa.ForeignKeyConstraint(["user_id"],["users.id"]),sa.ForeignKeyConstraint(["station_id"],["stations.id"]),sa.UniqueConstraint("endpoint",name="uq_push_subscriptions_endpoint"))
 op.create_index("ix_push_subscriptions_user_id","push_subscriptions",["user_id"],unique=False); op.create_index("ix_push_subscriptions_station_id","push_subscriptions",["station_id"],unique=False)
def downgrade():
 op.drop_index("ix_push_subscriptions_station_id",table_name="push_subscriptions"); op.drop_index("ix_push_subscriptions_user_id",table_name="push_subscriptions"); op.drop_table("push_subscriptions"); op.drop_column("kitchen_queue","overdue_notified_at")
