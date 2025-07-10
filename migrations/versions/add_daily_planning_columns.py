"""add daily planning columns

Revision ID: add_daily_planning_columns
Revises: 
Create Date: 2024-03-19

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_daily_planning_columns'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns for daily planning
    op.add_column('production', sa.Column('total_planned', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('production', sa.Column('monday_planned', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('production', sa.Column('tuesday_planned', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('production', sa.Column('wednesday_planned', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('production', sa.Column('thursday_planned', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('production', sa.Column('friday_planned', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('production', sa.Column('saturday_planned', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('production', sa.Column('sunday_planned', sa.Float(), nullable=True, server_default='0.0'))

def downgrade():
    # Remove the columns if needed
    op.drop_column('production', 'total_planned')
    op.drop_column('production', 'monday_planned')
    op.drop_column('production', 'tuesday_planned')
    op.drop_column('production', 'wednesday_planned')
    op.drop_column('production', 'thursday_planned')
    op.drop_column('production', 'friday_planned')
    op.drop_column('production', 'saturday_planned')
    op.drop_column('production', 'sunday_planned') 