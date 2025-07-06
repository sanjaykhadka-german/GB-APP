"""Add requirement_kg column to filling table

Revision ID: add_filling_requirement
Revises: abcdef123456
Create Date: 2024-03-19 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_filling_requirement'
down_revision = 'abcdef123456'
branch_labels = None
depends_on = None

def upgrade():
    # Add requirement_kg column to filling table if it doesn't exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    filling_columns = [col['name'] for col in inspector.get_columns('filling')]
    
    if 'requirement_kg' not in filling_columns:
        op.add_column('filling', sa.Column('requirement_kg', sa.Float(), nullable=True, server_default='0.0'))

def downgrade():
    # Remove requirement_kg column from filling table
    op.drop_column('filling', 'requirement_kg') 