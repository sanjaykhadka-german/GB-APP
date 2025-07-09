from app import app, db
from models.usage_report_table import UsageReportTable
from models.raw_material_report_table import RawMaterialReportTable
from models.inventory import Inventory
from models.production import Production
from models.recipe_master import RecipeMaster
from models.item_master import ItemMaster
from sqlalchemy import text
from decimal import Decimal

def verify_and_fix_reports():
    with app.app_context():
        try:
            print("Checking report tables...")
            
            # Check current counts
            usage_count = UsageReportTable.query.count()
            raw_material_count = RawMaterialReportTable.query.count()
            inventory_count = Inventory.query.count()
            
            print(f"\nCurrent record counts:")
            print(f"Usage Report Table: {usage_count}")
            print(f"Raw Material Report Table: {raw_material_count}")
            print(f"Inventory Table: {inventory_count}")
            
            # Clear existing data
            print("\nClearing existing report data...")
            UsageReportTable.query.delete()
            RawMaterialReportTable.query.delete()
            db.session.commit()
            
            # Get all production entries
            print("\nRegenerating reports from production data...")
            productions = Production.query.all()
            print(f"Found {len(productions)} production records")
            
            for prod in productions:
                if not prod.item:
                    continue
                    
                # Get recipe components
                components = RecipeMaster.query.filter_by(recipe_wip_id=prod.item.id).all()
                if not components:
                    continue
                    
                # Calculate recipe totals
                recipe_total = sum(Decimal(str(r.quantity_kg or 0)) for r in components)
                if recipe_total <= 0:
                    continue
                    
                print(f"\nProcessing production: {prod.production_code} ({prod.week_commencing})")
                print(f"Total recipe quantity: {recipe_total} kg")
                
                # Create usage reports for each component
                for recipe in components:
                    if not recipe.component_item:
                        continue
                        
                    recipe_qty = Decimal(str(recipe.quantity_kg or 0))
                    prod_total = Decimal(str(prod.total_kg or 0))
                    
                    usage_kg = float((recipe_qty / recipe_total) * prod_total)
                    percentage = float((recipe_qty / recipe_total) * 100)
                    
                    # Create usage report
                    usage_report = UsageReportTable(
                        week_commencing=prod.week_commencing,
                        production_date=prod.production_date,
                        recipe_code=prod.item.item_code,
                        raw_material=recipe.component_item.description,
                        usage_kg=usage_kg,
                        percentage=percentage
                    )
                    db.session.add(usage_report)
                    
                    # Create raw material report
                    raw_report = RawMaterialReportTable(
                        week_commencing=prod.week_commencing,
                        production_date=prod.production_date,
                        raw_material=recipe.component_item.description,
                        raw_material_id=recipe.component_item.id,
                        meat_required=usage_kg
                    )
                    db.session.add(raw_report)
                    
                    print(f"Added reports for {recipe.component_item.description}: {usage_kg:.2f} kg ({percentage:.2f}%)")
                    
                # Commit after each production to ensure data is saved
                db.session.commit()
                print("Committed changes to database")
            
            # Verify final counts
            final_usage_count = UsageReportTable.query.count()
            final_raw_material_count = RawMaterialReportTable.query.count()
            
            print("\nFinal record counts:")
            print(f"Usage Report Table: {final_usage_count}")
            print(f"Raw Material Report Table: {final_raw_material_count}")
            
            # Verify some sample data
            print("\nSample Usage Report records:")
            for record in UsageReportTable.query.limit(3).all():
                print(f"- {record.recipe_code}: {record.raw_material} ({record.usage_kg:.2f} kg)")
                
            print("\nSample Raw Material Report records:")
            for record in RawMaterialReportTable.query.limit(3).all():
                print(f"- {record.raw_material}: {record.meat_required:.2f} kg")
                
            print("\nReport regeneration completed successfully!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    verify_and_fix_reports() 