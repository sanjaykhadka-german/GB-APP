"""merge heads

Revision ID: b4a956dfd5af
Revises: b58485cf40fb, merge_report_tables_heads
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4a956dfd5af'
down_revision = ('b58485cf40fb', 'merge_report_tables_heads')
branch_labels = None
depends_on = None


def upgrade():
    # Make fg_code column nullable
    op.alter_column('soh', 'fg_code',
                    existing_type=sa.String(50),
                    nullable=True)


def downgrade():
    # Make fg_code column NOT NULL again
    op.alter_column('soh', 'fg_code',
                    existing_type=sa.String(50),
                    nullable=False)
