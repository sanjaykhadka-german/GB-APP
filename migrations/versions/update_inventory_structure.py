"""update inventory structure

Revision ID: update_inventory_structure
Revises: None
Create Date: 2025-07-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'update_inventory_structure'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Drop existing inventory table
    op.drop_table('inventory')
    
    # Create new inventory table
    op.create_table('inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_commencing', sa.Date(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('required_total', sa.Float(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('price_per_kg', sa.Float(), nullable=True),
        sa.Column('value_required', sa.Float(), nullable=True),
        sa.Column('current_stock', sa.Float(), nullable=True),
        sa.Column('supplier_name', sa.String(length=255), nullable=True),
        sa.Column('monday', sa.Float(), nullable=True, default=0),
        sa.Column('tuesday', sa.Float(), nullable=True, default=0),
        sa.Column('wednesday', sa.Float(), nullable=True, default=0),
        sa.Column('thursday', sa.Float(), nullable=True, default=0),
        sa.Column('friday', sa.Float(), nullable=True, default=0),
        sa.Column('saturday', sa.Float(), nullable=True, default=0),
        sa.Column('sunday', sa.Float(), nullable=True, default=0),
        sa.Column('required_for_plan', sa.Float(), nullable=True),
        sa.Column('variance_for_week', sa.Float(), nullable=True),
        sa.Column('variance', sa.Float(), nullable=True),
        sa.Column('to_be_ordered', sa.Float(), nullable=True),
        sa.Column('closing_stock', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['item_master.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('inventory') 