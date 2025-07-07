"""create report tables

Revision ID: create_report_tables
Revises: aa9c70c8f04d
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'create_report_tables'
down_revision = 'aa9c70c8f04d'
branch_labels = None
depends_on = None

def upgrade():
    # Create usage_report_table
    op.create_table('usage_report_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('week_commencing', sa.Date(), nullable=False),
        sa.Column('requirement_kg', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['item_master.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create raw_material_report_table
    op.create_table('raw_material_report_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('week_commencing', sa.Date(), nullable=False),
        sa.Column('requirement_kg', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['item_master.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('raw_material_report_table')
    op.drop_table('usage_report_table') 