from app import app, db
from sqlalchemy import text

def update_tables():
    with app.app_context():
        try:
            # Add department_id to packing table
            db.session.execute(text("""
                ALTER TABLE packing 
                ADD COLUMN department_id INT NULL,
                ALGORITHM=INPLACE;
            """))

            # Rename machinery to machinery_id in packing table
            db.session.execute(text("""
                ALTER TABLE packing
                CHANGE COLUMN machinery machinery_id INT NULL,
                ALGORITHM=INPLACE;
            """))

            # Add foreign key constraints to packing table
            db.session.execute(text("""
                ALTER TABLE packing
                ADD CONSTRAINT fk_packing_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL,
                ADD CONSTRAINT fk_packing_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL;
            """))

            # Add machinery_id and department_id to production table
            db.session.execute(text("""
                ALTER TABLE production 
                ADD COLUMN machinery_id INT NULL,
                ADD COLUMN department_id INT NULL,
                ADD CONSTRAINT fk_production_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL,
                ADD CONSTRAINT fk_production_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL;
            """))

            db.session.commit()
            print("Successfully updated tables")

        except Exception as e:
            db.session.rollback()
            print(f"Error updating tables: {str(e)}")

if __name__ == '__main__':
    update_tables() 