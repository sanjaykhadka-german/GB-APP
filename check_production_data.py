from app import app
from models.production import Production
from models.recipe_master import RecipeMaster
from datetime import datetime, timedelta, date

def check_production_data():
    with app.app_context():
        try:
            # Use specific week
            week_commencing = date(2025, 7, 14)
            
            print(f"\nChecking production data for week {week_commencing}")
            
            # Get all productions for this week
            productions = Production.query.filter_by(week_commencing=week_commencing).all()
            print(f"\nFound {len(productions)} production records")
            
            if productions:
                print("\nSample production records:")
                for prod in productions[:5]:
                    print(f"\nProduction {prod.id}:")
                    print(f"  Date: {prod.production_date}")
                    print(f"  Item: {prod.item.description if prod.item else 'N/A'}")
                    print(f"  Batches: {prod.batches}")
                    print(f"  Total KG: {prod.total_kg}")
                    
                    # Get recipes for this production
                    recipes = RecipeMaster.query.filter_by(recipe_wip_id=prod.item_id).all()
                    print(f"\n  Found {len(recipes)} recipes")
                    
                    for recipe in recipes:
                        print(f"\n  Recipe Component:")
                        print(f"    Component: {recipe.component_item.description if recipe.component_item else 'N/A'}")
                        print(f"    Quantity per batch: {recipe.quantity_kg}")
                        print(f"    Total usage: {float(recipe.quantity_kg) * float(prod.batches)}")
            
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    check_production_data() 