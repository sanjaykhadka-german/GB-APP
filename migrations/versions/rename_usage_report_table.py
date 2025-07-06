"""rename usage report table

Revision ID: rename_usage_report_table
Revises: aa9c70c8f04d
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'rename_usage_report_table'
down_revision = 'aa9c70c8f04d'
branch_labels = None
depends_on = None

def upgrade():
    # Check if table exists before renaming
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'usage_report' in inspector.get_table_names():
        op.rename_table('usage_report', 'usage_report_table')

def downgrade():
    # Check if table exists before renaming back
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'usage_report_table' in inspector.get_table_names():
        op.rename_table('usage_report_table', 'usage_report') 