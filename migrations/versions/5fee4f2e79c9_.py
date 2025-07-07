"""empty message

Revision ID: 5fee4f2e79c9
Revises: create_filling_production_tables, merge_heads_for_tables, update_filling_production_tables
Create Date: 2025-07-07 10:19:58.076576

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5fee4f2e79c9'
down_revision = ('create_filling_production_tables', 'merge_heads_for_tables', 'update_filling_production_tables')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
