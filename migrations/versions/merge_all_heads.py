"""merge all heads

Revision ID: merge_all_heads
Revises: 1234567890ab, add_wip_wipf_relationships, remove_temp_columns, rename_usage_report_table
Create Date: 2024-03-19 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_all_heads'
down_revision = ('1234567890ab', 'add_wip_wipf_relationships', 'remove_temp_columns', 'rename_usage_report_table')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass 