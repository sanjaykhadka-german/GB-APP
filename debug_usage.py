from app import app, db
from sqlalchemy.sql import text
from datetime import datetime

print("Starting debug...")

with app.app_context():
    try:
        # Test if we have any production records
        prod_query = "SELECT COUNT(*) FROM production"
        prod_count = db.session.execute(text(prod_query)).scalar()
        print(f"\nProduction records count: {prod_count}")

        if prod_count > 0:
            # Get sample production record
            sample_prod = db.session.execute(text("SELECT * FROM production LIMIT 1")).fetchone()
            print("\nSample production record:")
            print(f"ID: {sample_prod.id}")
            print(f"Production code: {sample_prod.production_code}")
            print(f"Production date: {sample_prod.production_date}")

        # Test if we have any recipe records
        recipe_query = "SELECT COUNT(*) FROM recipe_master"
        recipe_count = db.session.execute(text(recipe_query)).scalar()
        print(f"\nRecipe master records count: {recipe_count}")

        if recipe_count > 0:
            # Get sample recipe record
            sample_recipe = db.session.execute(text("SELECT * FROM recipe_master LIMIT 1")).fetchone()
            print("\nSample recipe record:")
            print(f"Recipe code: {sample_recipe.recipe_code}")
            print(f"Raw material ID: {sample_recipe.raw_material_id}")

        # Test the full join query
        test_query = """
        SELECT 
            p.production_date,
            p.production_code,
            r.recipe_code,
            r.raw_material_id,
            p.total_kg,
            r.percentage
        FROM production p
        JOIN recipe_master r ON p.production_code = r.recipe_code
        LIMIT 1
        """
        
        join_result = db.session.execute(text(test_query)).fetchone()
        if join_result:
            print("\nJoin query successful. Sample result:")
            print(f"Production date: {join_result.production_date}")
            print(f"Production code: {join_result.production_code}")
            print(f"Recipe code: {join_result.recipe_code}")
            print(f"Raw material ID: {join_result.raw_material_id}")
            print(f"Total kg: {join_result.total_kg}")
            print(f"Percentage: {join_result.percentage}")
        else:
            print("\nNo results from join query - possible issues:")
            print("1. No matching production_code between tables")
            print("2. Missing related records")

    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())
