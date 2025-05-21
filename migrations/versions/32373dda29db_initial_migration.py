"""Add priority column to packing table

Revision ID: <new_revision_id>
Revises: 32373dda29db
Create Date: 2025-05-20 15:49:00.123456
"""

from alembic import op
import sqlalchemy as sa

revision = '<new_revision_id>'
down_revision = '32373dda29db'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('packing', sa.Column('priority', sa.Integer(), nullable=False, server_default='0'))

def downgrade():
    op.drop_column('packing', 'priority')