from app import app
from database import db
from sqlalchemy import text

def add_description_column():
    try:
        # Execute the ALTER TABLE statement
        sql = text("ALTER TABLE raw_materials ADD COLUMN description VARCHAR(255) NULL")
        db.session.execute(sql)
        db.session.commit()
        print("Successfully added description column to raw_materials table")
    except Exception as e:
        print(f"Error adding description column: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    with app.app_context():
        add_description_column() 