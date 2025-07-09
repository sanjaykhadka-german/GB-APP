from app import app, db
from models.inventory import Inventory
from models.item_master import ItemMaster
from models.raw_material_stocktake import RawMaterialStocktake
from models.usage_report_table import UsageReportTable
from models.raw_material_report_table import RawMaterialReportTable
from models.recipe_master import RecipeMaster
from models.soh import SOH
from sqlalchemy import text
from decimal import Decimal
from datetime import datetime

def verify_and_fix_inventory():
    with app.app_context():
        try:
            print("Checking inventory table...")
            
            # Check current count
            inventory_count = Inventory.query.count()
            print(f"\nCurrent inventory count: {inventory_count}")
            
            # Clear existing data
            print("\nClearing existing inventory data...")
            Inventory.query.delete()
            db.session.commit()
            
            # Get all items that are used as components in recipes
            items = db.session.query(ItemMaster).join(
                RecipeMaster, RecipeMaster.component_item_id == ItemMaster.id
            ).filter(
                ~ItemMaster.item_code.like('%.%'),  # Exclude WIPF items
                ~ItemMaster.item_code.like('%WIP%')  # Exclude WIP items
            ).distinct().all()
            
            print(f"\nFound {len(items)} raw material items")
            
            # Get latest SOH week
            latest_soh = SOH.query.order_by(SOH.week_commencing.desc()).first()
            if not latest_soh:
                print("No SOH records found!")
                return
                
            week_commencing = latest_soh.week_commencing
            print(f"\nProcessing inventory for week: {week_commencing}")
            
            for item in items:
                print(f"\nProcessing item: {item.item_code} - {item.description}")
                
                # Get SOH data
                soh_record = SOH.query.filter_by(
                    item_id=item.id,
                    week_commencing=week_commencing
                ).first()
                
                # Get stocktake data
                stocktake = RawMaterialStocktake.query.filter_by(
                    item_code=item.item_code,
                    week_commencing=week_commencing
                ).first()
                
                # Get usage data
                usage = UsageReportTable.query.filter_by(
                    raw_material=item.description,
                    week_commencing=week_commencing
                ).all()
                
                total_usage = sum(u.usage_kg for u in usage) if usage else 0
                
                # Create inventory record
                inventory = Inventory(
                    raw_material_id=item.id,
                    week_commencing=week_commencing,
                    category_id=item.category_id or 1,  # Default to category 1 if none
                    price_per_kg=item.price_per_kg or 0.0,
                    required_total_production=total_usage,
                    current_stock=stocktake.current_stock if stocktake else 0,
                    supplier_name=item.supplier_name,
                    required_for_plan=total_usage,  # Same as required_total_production for now
                    variance_week=0.0,  # Will be calculated by property
                    kg_required=total_usage,  # Same as required_total_production for now
                    variance=0.0,  # Will be calculated by property
                    to_be_ordered=0.0,  # Will be calculated later
                    closing_stock=stocktake.current_stock if stocktake else 0,
                    created_at=datetime.utcnow()
                )
                
                db.session.add(inventory)
                print(f"Added inventory record:")
                print(f"- Current Stock: {inventory.current_stock}")
                print(f"- Required for Production: {inventory.required_total_production}")
                print(f"- Closing Stock: {inventory.closing_stock}")
                
                # Commit after each item
                db.session.commit()
                print("Committed to database")
            
            # Verify final count
            final_count = Inventory.query.count()
            print(f"\nFinal inventory count: {final_count}")
            
            # Show sample data
            print("\nSample inventory records:")
            for record in Inventory.query.limit(3).all():
                item = ItemMaster.query.get(record.raw_material_id)
                print(f"\n{item.description}:")
                print(f"- Week: {record.week_commencing}")
                print(f"- Current Stock: {record.current_stock}")
                print(f"- Required Total: {record.required_total_production}")
                print(f"- Required for Plan: {record.required_for_plan}")
                print(f"- Closing Stock: {record.closing_stock}")
            
            print("\nInventory regeneration completed successfully!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    verify_and_fix_inventory() 