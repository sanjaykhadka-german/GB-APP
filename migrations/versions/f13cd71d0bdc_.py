"""empty message

Revision ID: f13cd71d0bdc
Revises: 3ab19a553d04, 76d4a819a803, add_daily_planning_columns
Create Date: 2025-07-10 15:01:18.753198

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f13cd71d0bdc'
down_revision = ('3ab19a553d04', '76d4a819a803', 'add_daily_planning_columns')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
