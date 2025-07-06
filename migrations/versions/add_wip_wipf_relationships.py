"""Add WIP/WIPF relationships

Revision ID: add_wip_wipf_relationships
Revises: merge_multiple_heads_for_wip
Create Date: 2024-03-19 11:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_wip_wipf_relationships'
down_revision = 'merge_multiple_heads_for_wip'
branch_labels = None
depends_on = None

def upgrade():
    # Copy data from old columns to new ones
    op.execute("""
        UPDATE item_master 
        SET wip_component_id = wip_item_id 
        WHERE wip_item_id IS NOT NULL;
    """)
    
    op.execute("""
        UPDATE item_master 
        SET wipf_component_id = wipf_item_id 
        WHERE wipf_item_id IS NOT NULL;
    """)
    
    # Drop old columns
    op.drop_column('item_master', 'wip_item_id')
    op.drop_column('item_master', 'wipf_item_id')
    
    # Add foreign key constraints if they don't exist
    op.create_foreign_key(
        'fk_wip_component',
        'item_master', 'item_master',
        ['wip_component_id'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_wipf_component',
        'item_master', 'item_master',
        ['wipf_component_id'], ['id'],
        ondelete='SET NULL'
    )

def downgrade():
    # Remove foreign key constraints
    op.drop_constraint('fk_wip_component', 'item_master', type_='foreignkey')
    op.drop_constraint('fk_wipf_component', 'item_master', type_='foreignkey')
    
    # Add back old columns
    op.add_column('item_master', sa.Column('wip_item_id', sa.Integer(), nullable=True))
    op.add_column('item_master', sa.Column('wipf_item_id', sa.Integer(), nullable=True))
    
    # Copy data back to old columns
    op.execute("""
        UPDATE item_master 
        SET wip_item_id = wip_component_id 
        WHERE wip_component_id IS NOT NULL;
    """)
    
    op.execute("""
        UPDATE item_master 
        SET wipf_item_id = wipf_component_id 
        WHERE wipf_component_id IS NOT NULL;
    """) 