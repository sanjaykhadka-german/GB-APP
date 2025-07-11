from app import app, db
from models.item_master import ItemMaster
from models.item_type import ItemType
from models.production import Production
from models.recipe_master import RecipeMaster
from models.usage_report_table import UsageReportTable
from models.raw_material_report_table import RawMaterialReportTable
from sqlalchemy import func, text
from datetime import datetime, timedelta, date
from decimal import Decimal

def save_report_data(weeks_to_process):
    with app.app_context():
        try:
            if not weeks_to_process:
                print("save_report_data: No weeks provided to process. Skipping.")
                return

            print(f"Starting to save report data for weeks: {weeks_to_process}")
            
            for week_commencing in weeks_to_process:
                print(f"Processing week: {week_commencing}")
                # Clear existing data for this week
                db.session.execute(text("DELETE FROM raw_material_report_table WHERE week_commencing = :week"), {'week': week_commencing})
                db.session.execute(text("DELETE FROM usage_report_table WHERE week_commencing = :week"), {'week': week_commencing})
                db.session.commit()
                
                # Get all production records for this week
                productions = Production.query.filter_by(week_commencing=week_commencing).all()
                print(f"Found {len(productions)} production records for this week.")
                
                if not productions:
                    continue # Skip to the next week if no production records found
                
                # Process each production record
                for prod in productions:
                    if not prod.item or not prod.item.components:
                        continue
                        
                    print(f"  Processing production for item: {prod.item.description}")
                    
                    # Calculate total recipe quantity
                    total_recipe_qty = sum(float(r.quantity_kg or 0) for r in prod.item.components)
                    if total_recipe_qty <= 0:
                        continue
                    
                    # Process each component in the recipe
                    for recipe in prod.item.components:
                        if not recipe.component_item:
                            continue
                            
                        # Calculate usage and percentage
                        component_qty = float(recipe.quantity_kg or 0)
                        prod_qty = float(prod.total_kg or 0)
                        
                        usage_kg = (component_qty / total_recipe_qty) * prod_qty if total_recipe_qty > 0 else 0
                        percentage = (component_qty / total_recipe_qty) * 100 if total_recipe_qty > 0 else 0
                        
                        # Create usage report entry
                        usage_report = UsageReportTable(
                            week_commencing=week_commencing,
                            production_date=prod.production_date,
                            recipe_code=prod.item.item_code,
                            raw_material=recipe.component_item.description,
                            usage_kg=usage_kg,
                            percentage=percentage,
                            created_at=datetime.utcnow()
                        )
                        db.session.add(usage_report)
                        
                        # Create raw material report entry
                        raw_report = RawMaterialReportTable(
                            week_commencing=week_commencing,
                            production_date=prod.production_date,
                            raw_material_id=recipe.component_item.id,
                            raw_material=recipe.component_item.description,
                            meat_required=usage_kg,
                            created_at=datetime.utcnow()
                        )
                        db.session.add(raw_report)
                    
                # Commit after each production to ensure data is saved
                db.session.commit()
                print(f"    Saved report data for production of {prod.item.description}")
            
            print("\nReport data saving process completed!")
            
        except Exception as e:
            print(f"Error in save_report_data: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    # Example of how to run this manually for a specific week
    # You would need to pass a set or list of date objects
    specific_week = date(2025, 7, 14)
    save_report_data({specific_week}) 