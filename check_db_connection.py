import os
from dotenv import load_dotenv

print("1. Checking environment setup...")
load_dotenv()
db_uri = os.environ.get('SQLALCHEMY_DATABASE_URI')
print(f"Database URI found: {'Yes' if db_uri else 'No'}")
if db_uri:
    print(f"Database URI type: {db_uri[:db_uri.find(':')]}")  # Just show the database type (mysql, postgresql, etc.)

print("\n2. Trying to import Flask app...")
try:
    from app import create_app
    print("Successfully imported create_app")
    
    app = create_app()
    print("Successfully created app")
    
    with app.app_context():
        from database import db
        print("Successfully imported database")
        
        try:
            # Try a simple query
            from sqlalchemy.sql import text
            result = db.session.execute(text('SELECT 1'))
            print("Successfully connected to database")
            
            # Check tables
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
            """)
            tables = db.session.execute(tables_query).fetchall()
            print("\n3. Available tables:")
            for table in tables:
                print(f"- {table[0]}")
                
            # Check production table
            prod_count = db.session.execute(text("SELECT COUNT(*) FROM production")).scalar()
            print(f"\n4. Production records: {prod_count}")
            
            # Check recipe_master table
            recipe_count = db.session.execute(text("SELECT COUNT(*) FROM recipe_master")).scalar()
            print(f"5. Recipe master records: {recipe_count}")
            
        except Exception as e:
            print(f"Database query error: {str(e)}")
            
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    print(traceback.format_exc())
