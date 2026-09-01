"""restaurant flow v1
Revision ID: 8d8b8f2a1c90
Revises: c4d65860c4cd
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = '8d8b8f2a1c90'
down_revision: Union[str, Sequence[str], None] = 'c4d65860c4cd'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'station_id' not in {c['name'] for c in inspector.get_columns('categories')}:
        op.add_column('categories', sa.Column('station_id', sa.UUID(), nullable=True))
        op.create_foreign_key('fk_categories_station', 'categories', 'stations', ['station_id'], ['id'])
    if 'dishes' not in inspector.get_table_names():
        op.create_table('dishes',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(length=150), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('price', sa.Numeric(10,2), nullable=False),
            sa.Column('category_id', sa.UUID(), nullable=False),
            sa.Column('station_id', sa.UUID(), nullable=False),
            sa.Column('preparation_time', sa.Integer(), nullable=False),
            sa.Column('portion', sa.String(length=100), nullable=True),
            sa.Column('calories', sa.Integer(), nullable=False),
            sa.Column('image', sa.String(length=255), nullable=True),
            sa.Column('model_3d', sa.String(length=255), nullable=True),
            sa.Column('video', sa.String(length=255), nullable=True),
            sa.Column('ingredients', sa.Text(), nullable=True),
            sa.Column('allergens', sa.String(length=255), nullable=True),
            sa.Column('spicy_level', sa.Integer(), nullable=False),
            sa.Column('featured', sa.Boolean(), nullable=False),
            sa.Column('available', sa.Boolean(), nullable=False),
            sa.Column('active', sa.Boolean(), nullable=False),
            sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
            sa.ForeignKeyConstraint(['station_id'], ['stations.id']),
            sa.PrimaryKeyConstraint('id'))
    else:
        cols = {c['name'] for c in inspector.get_columns('dishes')}
        if 'portion' not in cols:
            op.add_column('dishes', sa.Column('portion', sa.String(length=100), nullable=True))
    op.add_column('order_items', sa.Column('dish_id', sa.UUID(), nullable=True))
    op.alter_column('order_items', 'product_id', nullable=True)
    op.create_foreign_key('fk_order_items_dish', 'order_items', 'dishes', ['dish_id'], ['id'])
    op.create_table('waiter_calls',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('table_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=True),
        sa.Column('waiter_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attended_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['table_id'], ['tables.id']),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id']),
        sa.ForeignKeyConstraint(['waiter_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'))
    op.create_table('screens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('station_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=80), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id']),
        sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('code'))

def downgrade():
    op.drop_constraint('fk_categories_station', 'categories', type_='foreignkey')
    op.drop_column('categories', 'station_id')
    op.drop_constraint('fk_order_items_dish', 'order_items', type_='foreignkey')
    op.drop_column('order_items', 'dish_id')
    op.alter_column('order_items', 'product_id', nullable=False)
    op.drop_table('screens'); op.drop_table('waiter_calls')
    if 'dishes' in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table('dishes')
