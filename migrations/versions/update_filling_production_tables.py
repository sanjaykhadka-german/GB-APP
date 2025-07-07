"""Update filling and production tables

Revision ID: update_filling_production_tables
Revises: add_filling_requirement
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'update_filling_production_tables'
down_revision = 'add_filling_requirement'
branch_labels = None
depends_on = None

def upgrade():
    # Add missing columns to filling table if they don't exist
    with op.batch_alter_table('filling') as batch_op:
        # Add columns only if they don't exist
        try:
            batch_op.add_column(sa.Column('kilo_per_size', sa.Float(), nullable=True, default=0.0))
        except Exception:
            pass

    # Add missing columns to production table if they don't exist
    with op.batch_alter_table('production') as batch_op:
        # Add columns only if they don't exist
        try:
            batch_op.add_column(sa.Column('week_commencing', sa.Date(), nullable=True))
        except Exception:
            pass
            
        try:
            batch_op.add_column(sa.Column('requirement_kg', sa.Float(), nullable=True, default=0.0))
        except Exception:
            pass
            
        try:
            batch_op.add_column(sa.Column('priority', sa.Integer(), nullable=True, default=0))
        except Exception:
            pass

def downgrade():
    # Remove added columns from filling table
    with op.batch_alter_table('filling') as batch_op:
        batch_op.drop_column('kilo_per_size')

    # Remove added columns from production table
    with op.batch_alter_table('production') as batch_op:
        batch_op.drop_column('week_commencing')
        batch_op.drop_column('requirement_kg')
        batch_op.drop_column('priority') 