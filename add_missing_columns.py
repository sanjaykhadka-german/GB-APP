from app import app
from database import db
from sqlalchemy import text

def add_missing_columns():
    try:
        # List of columns to add with their definitions
        columns = [
            ("category_id", "INT, ADD CONSTRAINT fk_category FOREIGN KEY (category_id) REFERENCES category(id)"),
            ("uom_id", "INT, ADD CONSTRAINT fk_uom FOREIGN KEY (uom_id) REFERENCES uom_type(UOMID)"),
            ("min_level", "FLOAT"),
            ("max_level", "FLOAT"),
            ("price_per_kg", "FLOAT"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        ]
        
        # Add each column if it doesn't exist
        for column_name, definition in columns:
            try:
                sql = text(f"ALTER TABLE raw_materials ADD COLUMN {column_name} {definition}")
                db.session.execute(sql)
                db.session.commit()
                print(f"Successfully added {column_name} column")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print(f"Column {column_name} already exists")
                else:
                    print(f"Error adding {column_name} column: {str(e)}")
                db.session.rollback()
        
        print("Finished adding missing columns")
        
    except Exception as e:
        print(f"Error in add_missing_columns: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    with app.app_context():
        add_missing_columns() 