"""Add product_description to joining table

Revision ID: d956e5167e0a
Revises: 06755879b096
Create Date: 2025-05-16 08:55:52.598914

"""
from alembic import op
import sqlalchemy as sa

revision = 'd956e5167e0a'
down_revision = '06755879b096'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('joining', sa.Column('product_description', sa.String(255), nullable=True))

def downgrade():
    op.drop_column('joining', 'product_description')