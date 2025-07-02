from app import app, db
from sqlalchemy import text

def remove_redundant_columns():
    with app.app_context():
        try:
            # First, verify that all records have valid item_id
            result = db.session.execute(text("""
                SELECT COUNT(*) as count 
                FROM filling 
                WHERE item_id IS NULL OR item_id NOT IN (SELECT id FROM item_master)
            """))
            invalid_count = result.fetchone()[0]
            
            if invalid_count > 0:
                print(f"Error: Found {invalid_count} records without valid item_id. Please fix these before removing columns.")
                return

            # Remove the redundant columns
            db.session.execute(text("""
                ALTER TABLE filling
                DROP COLUMN fill_code,
                DROP COLUMN description;
            """))

            db.session.commit()
            print("Successfully removed redundant columns from filling table")

        except Exception as e:
            db.session.rollback()
            print(f"Error removing columns: {str(e)}")

if __name__ == '__main__':
    remove_redundant_columns() 