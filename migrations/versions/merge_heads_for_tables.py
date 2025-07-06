"""merge heads for tables

Revision ID: merge_heads_for_tables
Revises: create_filling_production_tables_v2, add_filling_requirement
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'merge_heads_for_tables'
down_revision = None
branch_labels = None
depends_on = None

# Multiple heads being merged
depends_on = ['create_filling_production_tables_v2', 'add_filling_requirement']

def upgrade():
    pass

def downgrade():
    pass 