from app import app, db
from sqlalchemy import text

def verify_tables():
    with app.app_context():
        try:
            # Check packing table structure
            result = db.session.execute(text("DESCRIBE packing"))
            print("\nPacking table structure:")
            for row in result:
                print(row)

            # Check production table structure
            result = db.session.execute(text("DESCRIBE production"))
            print("\nProduction table structure:")
            for row in result:
                print(row)

            # Check foreign key constraints
            result = db.session.execute(text("""
                SELECT CONSTRAINT_NAME, TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME 
                FROM information_schema.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = 'gbdb' 
                AND REFERENCED_TABLE_NAME IN ('machinery', 'department')
                AND TABLE_NAME IN ('packing', 'production');
            """))
            print("\nForeign key constraints:")
            for row in result:
                print(row)

        except Exception as e:
            print(f"Error verifying tables: {str(e)}")

if __name__ == '__main__':
    verify_tables() 