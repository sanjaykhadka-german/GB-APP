from app import app, db
from sqlalchemy import text

def fix_usage_report_table():
    with app.app_context():
        try:
            print("Fixing usage_report_table structure...")
            
            # Drop existing table
            db.session.execute(text("DROP TABLE IF EXISTS usage_report_table"))
            db.session.commit()
            
            # Create new table with correct structure
            create_table_sql = """
            CREATE TABLE usage_report_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                week_commencing DATE,
                production_date DATE NOT NULL,
                recipe_code VARCHAR(50) NOT NULL,
                raw_material VARCHAR(255) NOT NULL,
                usage_kg FLOAT NOT NULL,
                percentage FLOAT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            db.session.execute(text(create_table_sql))
            db.session.commit()
            
            print("Usage report table structure updated successfully!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    fix_usage_report_table() 