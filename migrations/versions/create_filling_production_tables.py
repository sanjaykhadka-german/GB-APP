"""Create filling and production tables

Revision ID: create_filling_production_tables
Revises: add_filling_requirement
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'create_filling_production_tables'
down_revision = 'add_filling_requirement'
branch_labels = None
depends_on = None

def upgrade():
    # Create filling table
    op.create_table(
        'filling',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('week_commencing', sa.Date(), nullable=True),
        sa.Column('filling_date', sa.Date(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('machinery_id', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('kilo_per_size', sa.Float(), nullable=True, default=0.0),
        sa.Column('requirement_kg', sa.Float(), nullable=True, default=0.0),
        sa.ForeignKeyConstraint(['item_id'], ['item_master.id']),
        sa.ForeignKeyConstraint(['machinery_id'], ['machinery.machineID'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['department_id'], ['department.department_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create production table
    op.create_table(
        'production',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('week_commencing', sa.Date(), nullable=True),
        sa.Column('production_date', sa.Date(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('machinery_id', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('production_code', sa.String(50), nullable=True),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('batches', sa.Float(), nullable=True, default=0.0),
        sa.Column('total_kg', sa.Float(), nullable=True, default=0.0),
        sa.Column('requirement_kg', sa.Float(), nullable=True, default=0.0),
        sa.Column('priority', sa.Integer(), nullable=True, default=0),
        sa.ForeignKeyConstraint(['item_id'], ['item_master.id']),
        sa.ForeignKeyConstraint(['machinery_id'], ['machinery.machineID'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['department_id'], ['department.department_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('production')
    op.drop_table('filling') 