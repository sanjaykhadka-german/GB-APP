"""merge heads for tables

Revision ID: merge_heads_for_tables
Revises: create_filling_production_tables, create_filling_production_tables_v2
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'merge_heads_for_tables'
down_revision = ('create_filling_production_tables', 'create_filling_production_tables_v2')
branch_labels = None
depends_on = None

def upgrade():
    # Create packing_allergen table
    op.create_table('packing_allergen',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('packing_id', sa.Integer(), nullable=False),
        sa.Column('allergen_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['packing_id'], ['packing.id'], ),
        sa.ForeignKeyConstraint(['allergen_id'], ['allergen.allergens_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('packing_id', 'allergen_id', name='uix_packing_allergen')
    )

def downgrade():
    # Drop packing_allergen table
    op.drop_table('packing_allergen') 