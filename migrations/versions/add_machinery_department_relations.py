"""Add machinery and department relations

Revision ID: 1234567890ab
Revises: resolve_migration_cycle
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '1234567890ab'
down_revision = 'resolve_migration_cycle'
branch_labels = None
depends_on = None

def upgrade():
    # Check if columns exist before adding them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Get existing columns for each table
    soh_columns = [col['name'] for col in inspector.get_columns('soh')]
    filling_columns = [col['name'] for col in inspector.get_columns('filling')]
    packing_columns = [col['name'] for col in inspector.get_columns('packing')]
    production_columns = [col['name'] for col in inspector.get_columns('production')]
    
    # SOH table
    alter_statements = []
    if 'machinery_id' not in soh_columns:
        alter_statements.append("ADD COLUMN machinery_id INT NULL")
        alter_statements.append("ADD CONSTRAINT fk_soh_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL")
    if 'department_id' not in soh_columns:
        alter_statements.append("ADD COLUMN department_id INT NULL")
        alter_statements.append("ADD CONSTRAINT fk_soh_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL")
    if alter_statements:
        op.execute(f"""
            ALTER TABLE soh
            {','.join(alter_statements)}
        """)

    # Filling table
    alter_statements = []
    if 'machinery_id' not in filling_columns:
        alter_statements.append("ADD COLUMN machinery_id INT NULL")
        alter_statements.append("ADD CONSTRAINT fk_filling_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL")
    if 'department_id' not in filling_columns:
        alter_statements.append("ADD COLUMN department_id INT NULL")
        alter_statements.append("ADD CONSTRAINT fk_filling_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL")
    if alter_statements:
        op.execute(f"""
            ALTER TABLE filling
            {','.join(alter_statements)}
        """)

    # Packing table
    alter_statements = []
    if 'department_id' not in packing_columns:
        alter_statements.append("ADD COLUMN department_id INT NULL")
        alter_statements.append("ADD CONSTRAINT fk_packing_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL")
    if 'machinery' in packing_columns and 'machinery_id' not in packing_columns:
        alter_statements.append("CHANGE COLUMN machinery machinery_id INT NULL")
        alter_statements.append("ADD CONSTRAINT fk_packing_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL")
    if alter_statements:
        op.execute(f"""
            ALTER TABLE packing
            {','.join(alter_statements)}
        """)

    # Production table
    alter_statements = []
    if 'machinery_id' not in production_columns:
        alter_statements.append("ADD COLUMN machinery_id INT NULL")
        alter_statements.append("ADD CONSTRAINT fk_production_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL")
    if 'department_id' not in production_columns:
        alter_statements.append("ADD COLUMN department_id INT NULL")
        alter_statements.append("ADD CONSTRAINT fk_production_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL")
    if alter_statements:
        op.execute(f"""
            ALTER TABLE production
            {','.join(alter_statements)}
        """)

def downgrade():
    # Remove foreign key constraints first
    op.execute("""
        ALTER TABLE soh
        DROP FOREIGN KEY IF EXISTS fk_soh_machinery,
        DROP FOREIGN KEY IF EXISTS fk_soh_department,
        DROP COLUMN IF EXISTS machinery_id,
        DROP COLUMN IF EXISTS department_id
    """)

    # Remove from Filling
    op.execute("""
        ALTER TABLE filling 
        DROP FOREIGN KEY fk_filling_machinery,
        DROP FOREIGN KEY fk_filling_department,
        DROP COLUMN machinery_id,
        DROP COLUMN department_id
    """)

    # Revert Packing
    op.execute("""
        ALTER TABLE packing 
        DROP FOREIGN KEY fk_packing_machinery,
        DROP FOREIGN KEY fk_packing_department,
        CHANGE COLUMN machinery_id machinery INT NULL,
        DROP COLUMN department_id
    """)

    # Remove from Production
    op.execute("""
        ALTER TABLE production 
        DROP FOREIGN KEY fk_production_machinery,
        DROP FOREIGN KEY fk_production_department,
        DROP COLUMN machinery_id,
        DROP COLUMN department_id
    """) 