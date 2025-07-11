from sqlalchemy import text
from database import db
from app import create_app
import os

def create_inventory_table():
    try:
        # Read the SQL file
        with open('create_new_inventory_table.sql', 'r') as file:
            sql = file.read()
        
        # Split SQL into separate statements
        sql_statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
        
        # Create app and execute SQL within app context
        app = create_app()
        with app.app_context():
            with db.engine.connect() as conn:
                for statement in sql_statements:
                    conn.execute(text(statement))
                conn.commit()
            
        print("Successfully created inventory table")
        
    except Exception as e:
        print(f"Error creating inventory table: {str(e)}")
        
if __name__ == "__main__":
    create_inventory_table() 