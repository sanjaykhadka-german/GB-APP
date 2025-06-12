from app import app
from database import db
from sqlalchemy import text

def add_department_column():
    try:
        # Add department_id column with foreign key constraint
        sql = text("""
            ALTER TABLE raw_materials 
            ADD COLUMN department_id INT,
            ADD CONSTRAINT fk_department 
            FOREIGN KEY (department_id) 
            REFERENCES department(department_id)
        """)
        db.session.execute(sql)
        db.session.commit()
        print("Successfully added department_id column")
        
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("Column department_id already exists")
        else:
            print(f"Error adding department_id column: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    with app.app_context():
        add_department_column() 