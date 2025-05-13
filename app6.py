"""Add date_time column to SOH table

Revision ID: <some_revision_id>
Revises: <previous_revision_id>
Create Date: <date>
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '<some_revision_id>'
down_revision = '<previous_revision_id>'
branch_labels = None
depends_on = None

def upgrade():
    # Add the date_time column to the soh table
    op.add_column('soh', sa.Column('date_time', sa.DateTime(), nullable=True, server_default=sa.func.current_timestamp()))

def downgrade():
    # Remove the date_time column in case of rollback
    op.drop_column('soh', 'date_time')

