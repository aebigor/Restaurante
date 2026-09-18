"""delivery dashboard, courier tracking, chat and payment handoff"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='f3b7c9d1e2a4'
down_revision='e1f4a8c9b7d2'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('orders', sa.Column('delivery_fee', sa.Float(), nullable=False, server_default='0'))
    op.add_column('orders', sa.Column('delivery_code', sa.String(length=12), nullable=True))
    op.add_column('orders', sa.Column('courier_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('orders', sa.Column('courier_assigned_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('orders', sa.Column('courier_started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('orders', sa.Column('courier_delivered_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('orders', sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('orders', sa.Column('cancellation_reason', sa.String(length=300), nullable=True))
    op.add_column('orders', sa.Column('payment_method', sa.String(length=30), nullable=True))
    op.add_column('orders', sa.Column('payment_confirmed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key('fk_orders_courier_id_users','orders','users',['courier_id'],['id'])
    op.create_index('ix_orders_courier_id','orders',['courier_id'])
    op.create_table('courier_locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('courier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False), sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=True), sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index('ix_courier_locations_courier_id','courier_locations',['courier_id'])
    op.create_index('ix_courier_locations_recorded_at','courier_locations',['recorded_at'])
    op.create_table('delivery_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id'), nullable=True),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('message', sa.Text(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index('ix_delivery_messages_order_id','delivery_messages',['order_id'])
    op.create_index('ix_delivery_messages_created_at','delivery_messages',['created_at'])

def downgrade():
    op.drop_index('ix_delivery_messages_created_at', table_name='delivery_messages'); op.drop_index('ix_delivery_messages_order_id', table_name='delivery_messages'); op.drop_table('delivery_messages')
    op.drop_index('ix_courier_locations_recorded_at', table_name='courier_locations'); op.drop_index('ix_courier_locations_courier_id', table_name='courier_locations'); op.drop_table('courier_locations')
    op.drop_index('ix_orders_courier_id', table_name='orders'); op.drop_constraint('fk_orders_courier_id_users','orders',type_='foreignkey')
    for c in ['payment_confirmed_at','payment_method','cancellation_reason','cancelled_at','courier_delivered_at','courier_started_at','courier_assigned_at','courier_id','delivery_code','delivery_fee']:
        op.drop_column('orders',c)
