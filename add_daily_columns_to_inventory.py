"""
Migration script to add daily columns to inventory table
"""
from app import app
from database import db
from sqlalchemy import text

def add_daily_columns():
    with app.app_context():
        try:
            # Add daily columns to inventory table
            daily_columns = [
                'monday DECIMAL(10,2) DEFAULT 0.00',
                'tuesday DECIMAL(10,2) DEFAULT 0.00', 
                'wednesday DECIMAL(10,2) DEFAULT 0.00',
                'thursday DECIMAL(10,2) DEFAULT 0.00',
                'friday DECIMAL(10,2) DEFAULT 0.00',
                'saturday DECIMAL(10,2) DEFAULT 0.00',
                'sunday DECIMAL(10,2) DEFAULT 0.00'
            ]
            
            for column in daily_columns:
                column_name = column.split()[0]
                
                # Check if column exists
                check_sql = text(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = 'inventory' 
                    AND column_name = '{column_name}'
                """)
                
                result = db.session.execute(check_sql).scalar()
                
                if result == 0:
                    # Add the column
                    alter_sql = text(f"ALTER TABLE inventory ADD COLUMN {column}")
                    db.session.execute(alter_sql)
                    print(f"Added column: {column_name}")
                else:
                    print(f"Column {column_name} already exists")
            
            db.session.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    add_daily_columns() 