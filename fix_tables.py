from app import app, db
from models.filling import Filling
from models.production import Production
from sqlalchemy import text, inspect

def check_and_fix_tables():
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            
            # Check if tables exist
            existing_tables = inspector.get_table_names()
            print("\nExisting tables:", existing_tables)
            
            # Check filling table
            if 'filling' not in existing_tables:
                print("\nCreating filling table...")
                Filling.__table__.create(db.engine)
                print("Filling table created successfully")
            else:
                print("\nFilling table exists, checking columns...")
                columns = {c['name'] for c in inspector.get_columns('filling')}
                print("Existing columns:", columns)
                
                # Add missing columns if any
                required_columns = {
                    'id', 'week_commencing', 'filling_date', 'item_id',
                    'machinery_id', 'department_id', 'kilo_per_size', 'requirement_kg'
                }
                
                missing = required_columns - columns
                if missing:
                    print(f"Missing columns in filling table: {missing}")
                    for col in missing:
                        if col == 'week_commencing':
                            db.session.execute(text("ALTER TABLE filling ADD COLUMN week_commencing DATE"))
                        elif col in ('kilo_per_size', 'requirement_kg'):
                            db.session.execute(text(f"ALTER TABLE filling ADD COLUMN {col} FLOAT DEFAULT 0.0"))
                    db.session.commit()
                    print("Added missing columns to filling table")
            
            # Check production table
            if 'production' not in existing_tables:
                print("\nCreating production table...")
                Production.__table__.create(db.engine)
                print("Production table created successfully")
            else:
                print("\nProduction table exists, checking columns...")
                columns = {c['name'] for c in inspector.get_columns('production')}
                print("Existing columns:", columns)
                
                # Add missing columns if any
                required_columns = {
                    'id', 'week_commencing', 'production_date', 'item_id',
                    'machinery_id', 'department_id', 'production_code',
                    'description', 'batches', 'total_kg', 'requirement_kg', 'priority'
                }
                
                missing = required_columns - columns
                if missing:
                    print(f"Missing columns in production table: {missing}")
                    for col in missing:
                        if col == 'week_commencing':
                            db.session.execute(text("ALTER TABLE production ADD COLUMN week_commencing DATE"))
                        elif col in ('batches', 'total_kg', 'requirement_kg'):
                            db.session.execute(text(f"ALTER TABLE production ADD COLUMN {col} FLOAT DEFAULT 0.0"))
                        elif col == 'priority':
                            db.session.execute(text(f"ALTER TABLE production ADD COLUMN {col} INTEGER DEFAULT 0"))
                        elif col == 'production_code':
                            db.session.execute(text(f"ALTER TABLE production ADD COLUMN {col} VARCHAR(50)"))
                        elif col == 'description':
                            db.session.execute(text(f"ALTER TABLE production ADD COLUMN {col} VARCHAR(255)"))
                    db.session.commit()
                    print("Added missing columns to production table")
            
            print("\n✅ Tables check and fix completed successfully")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    check_and_fix_tables() 