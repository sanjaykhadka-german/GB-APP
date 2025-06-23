from app import app
from database import db
from models.raw_material_stocktake import RawMaterialStocktake

def create_stocktake_table():
    """Create the raw_material_stocktake table"""
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            print("Successfully created raw_material_stocktake table")
            
            # Check if table was created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'raw_material_stocktake' in tables:
                print("✓ raw_material_stocktake table exists in database")
                
                # Show table structure
                columns = inspector.get_columns('raw_material_stocktake')
                print("\nTable structure:")
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
                    
            else:
                print("✗ raw_material_stocktake table was not created")
                
        except Exception as e:
            print(f"Error creating table: {str(e)}")

if __name__ == "__main__":
    create_stocktake_table() 