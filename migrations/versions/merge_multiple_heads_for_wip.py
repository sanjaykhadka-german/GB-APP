"""merge multiple heads for wip

Revision ID: merge_multiple_heads_for_wip
Revises: aa9c70c8f04d, 7d4f834a7895
Create Date: 2024-03-19 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_multiple_heads_for_wip'
down_revision = ('aa9c70c8f04d', '7d4f834a7895')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass 