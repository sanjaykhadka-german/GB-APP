from app import create_app, db
from sqlalchemy import inspect

def check_table_structure():
    """Check the structure of all tables in the database"""
    inspector = inspect(db.engine)
    
    for table_name in inspector.get_table_names():
        print(f"\n{table_name}:")
        for column in inspector.get_columns(table_name):
            print(f"  {column['name']}: {column['type']}")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        check_table_structure() 