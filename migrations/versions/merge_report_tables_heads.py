"""merge report tables heads

Revision ID: merge_report_tables_heads
Revises: create_report_tables, aa9c70c8f04d
Create Date: 2024-03-19 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_report_tables_heads'
down_revision = ('create_report_tables', 'aa9c70c8f04d')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass 