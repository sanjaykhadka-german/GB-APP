import sys
print("Python version:", sys.version)

try:
    print("Importing modules...")
    from app import app
    print("App imported")
    from database import db
    print("Database imported")
    from sqlalchemy.sql import text
    print("SQLAlchemy imported")

    print("\nStarting app context...")
    with app.app_context():
        try:
        # Test production table
        prod_result = db.session.execute(text('SELECT COUNT(*) FROM production'))
        print(f'Production records: {prod_result.scalar()}')
        
        # Test recipe_master table
        recipe_result = db.session.execute(text('SELECT COUNT(*) FROM recipe_master'))
        print(f'Recipe records: {recipe_result.scalar()}')
        
        # Test raw_materials table
        raw_mat_result = db.session.execute(text('SELECT COUNT(*) FROM raw_materials'))
        print(f'Raw materials records: {raw_mat_result.scalar()}')
        
        # Test the full join
        full_result = db.session.execute(text('''
            SELECT COUNT(*) 
            FROM production p 
            JOIN recipe_master r ON p.production_code = r.recipe_code 
            JOIN raw_materials rm ON r.raw_material_id = rm.id
        '''))
        print(f'Combined records: {full_result.scalar()}')
        
        # Get a sample record
        sample = db.session.execute(text('''
            SELECT 
                p.production_date,
                p.production_code,
                rm.raw_material,
                p.total_kg,
                r.percentage
            FROM production p 
            JOIN recipe_master r ON p.production_code = r.recipe_code 
            JOIN raw_materials rm ON r.raw_material_id = rm.id
            LIMIT 1
        ''')).fetchone()
        
        if sample:
            print("\nSample record:")
            print(f"Production date: {sample.production_date}")
            print(f"Production code: {sample.production_code}")
            print(f"Raw material: {sample.raw_material}")
            print(f"Total kg: {sample.total_kg}")
            print(f"Percentage: {sample.percentage}")
        else:
            print("\nNo sample record found")
            
    except Exception as e:
        print(f"Error: {str(e)}")
