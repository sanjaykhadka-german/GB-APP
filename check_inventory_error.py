from app import app
from database import db
from models.raw_material_stocktake import RawMaterialStocktake
from models.raw_material_report_table import RawMaterialReportTable
from models.item_master import ItemMaster
from models.item_type import ItemType
from datetime import datetime, timedelta

def check_inventory_error():
    with app.app_context():
        try:
            print("Checking inventory initialization process...")
            
            # Get a sample week
            week = RawMaterialStocktake.query.with_entities(
                RawMaterialStocktake.week_commencing
            ).first()
            
            if not week:
                print("No stocktake records found")
                return
                
            print(f"\nChecking week: {week.week_commencing}")
            
            # Get all stocktake records for this week
            stocktakes = RawMaterialStocktake.query.filter_by(
                week_commencing=week.week_commencing
            ).all()
            
            print(f"Found {len(stocktakes)} stocktake records")
            
            # Check each stocktake record's relationships
            for stocktake in stocktakes:
                print(f"\nChecking item: {stocktake.item_code}")
                
                # Check if item exists in ItemMaster
                item = ItemMaster.query.filter_by(item_code=stocktake.item_code).first()
                if not item:
                    print(f"ERROR: Item not found in ItemMaster")
                    continue
                    
                print(f"ItemMaster record found: {item.id} - {item.description}")
                
                # Check if report exists
                report = RawMaterialReportTable.query.filter_by(
                    week_commencing=week.week_commencing,
                    item_id=item.id
                ).first()
                
                if not report:
                    print(f"WARNING: No report found for this item")
                else:
                    print(f"Report found: {report.id}")
                    print(f"Required total: {report.required_total_production}")
                    print(f"Current stock: {report.current_stock}")
                
        except Exception as e:
            print(f"Error during check: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    check_inventory_error() 