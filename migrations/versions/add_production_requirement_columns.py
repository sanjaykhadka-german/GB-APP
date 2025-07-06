"""Add requirement_kg and priority columns to production table

Revision ID: abcdef123456
Revises: merge_all_heads
Create Date: 2024-03-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'abcdef123456'
down_revision = 'merge_all_heads'
branch_labels = None
depends_on = None

def upgrade():
    # Check if columns exist before adding them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    production_columns = [col['name'] for col in inspector.get_columns('production')]
    
    # Build the ALTER TABLE statement dynamically
    alter_statements = []
    
    if 'requirement_kg' not in production_columns:
        alter_statements.append("ADD COLUMN requirement_kg FLOAT DEFAULT 0.0")
        
    if 'priority' not in production_columns:
        alter_statements.append("ADD COLUMN priority INT DEFAULT 0")
    
    if alter_statements:
        op.execute(f"""
            ALTER TABLE production
            {','.join(alter_statements)}
        """)

    # Copy total_kg values to requirement_kg for existing records
    op.execute('UPDATE production SET requirement_kg = total_kg WHERE requirement_kg IS NULL')

def downgrade():
    # Remove the new columns
    op.execute("""
        ALTER TABLE production
        DROP COLUMN IF EXISTS requirement_kg,
        DROP COLUMN IF EXISTS priority
    """) 