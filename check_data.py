from app import app
from database import db
from models import Production, RecipeMaster, UsageReport, RawMaterials
from datetime import datetime, timedelta

def check_data():
    with app.app_context():
        # Check Production records
        production_count = Production.query.count()
        print(f"\nProduction Records: {production_count}")
        if production_count > 0:
            sample_prod = Production.query.first()
            print("Sample Production record:")
            print(f"Date: {sample_prod.production_date}")
            print(f"Code: {sample_prod.production_code}")
            print(f"Total KG: {sample_prod.total_kg}")
        
        # Check Recipe records
        recipe_count = RecipeMaster.query.count()
        print(f"\nRecipe Records: {recipe_count}")
        if recipe_count > 0:
            sample_recipe = RecipeMaster.query.first()
            print("Sample Recipe record:")
            print(f"Code: {sample_recipe.recipe_code}")
            print(f"Description: {sample_recipe.description}")
            print(f"KG per batch: {sample_recipe.kg_per_batch}")
            print(f"Percentage: {sample_recipe.percentage}")
        
        # Check Raw Materials
        raw_materials_count = RawMaterials.query.count()
        print(f"\nRaw Materials Records: {raw_materials_count}")
        if raw_materials_count > 0:
            sample_raw = RawMaterials.query.first()
            print("Sample Raw Material record:")
            print(f"Name: {sample_raw.raw_material}")
        
        # Check Usage Reports
        usage_count = UsageReport.query.count()
        print(f"\nUsage Report Records: {usage_count}")
        if usage_count > 0:
            sample_usage = UsageReport.query.first()
            print("Sample Usage Report record:")
            print(f"Date: {sample_usage.production_date}")
            print(f"Recipe Code: {sample_usage.recipe_code}")
            print(f"Raw Material: {sample_usage.raw_material}")
            print(f"Usage KG: {sample_usage.usage_kg}")
            print(f"Percentage: {sample_usage.percentage}")

if __name__ == "__main__":
    check_data() 