from app import create_app
from database import db
from models.inventory import Inventory
from models.raw_material_report_table import RawMaterialReportTable
from models.raw_material_stocktake import RawMaterialStocktake
from models.item_master import ItemMaster
from datetime import datetime
from decimal import Decimal

def populate_inventory():
    try:
        app = create_app()
        with app.app_context():
            print("Starting inventory population...")
            
            # Get all unique week_commencing dates from raw_material_report_table
            weeks = RawMaterialReportTable.query.with_entities(
                RawMaterialReportTable.week_commencing
            ).distinct().all()
            
            # Get all items from item_master that have reports
            items = ItemMaster.query.join(
                RawMaterialReportTable,
                ItemMaster.id == RawMaterialReportTable.item_id
            ).distinct().all()
            
            print(f"Found {len(weeks)} weeks and {len(items)} items")
            
            # For each week and item combination
            for week in weeks:
                week_date = week[0]
                print(f"\nProcessing week: {week_date}")
                
                for item in items:
                    print(f"Processing item: {item.description}")
                    
                    # Check if inventory entry already exists
                    existing = Inventory.query.filter_by(
                        week_commencing=week_date,
                        item_id=item.id
                    ).first()
                    
                    if existing:
                        print(f"Entry already exists for {item.description} in week {week_date}")
                        continue
                    
                    # Get raw material report data
                    report = RawMaterialReportTable.query.filter_by(
                        week_commencing=week_date,
                        item_id=item.id
                    ).first()
                    
                    # Get stocktake data - if none exists, use 0
                    stocktake = RawMaterialStocktake.query.filter_by(
                        item_code=item.item_code
                    ).order_by(RawMaterialStocktake.week_commencing.desc()).first()
                    
                    # Convert decimal values to float
                    required_total = float(report.required_total_production) if report and report.required_total_production else 0.0
                    price_per_kg = float(item.price_per_kg) if item.price_per_kg else 0.0
                    current_stock = float(stocktake.current_stock) if stocktake and stocktake.current_stock else 0.0
                    
                    # Create new inventory entry
                    inventory = Inventory(
                        week_commencing=week_date,
                        item_id=item.id,
                        required_total=required_total,
                        price_per_kg=price_per_kg,
                        current_stock=current_stock,
                        supplier_name=item.supplier_name
                    )
                    
                    # Calculate initial values
                    inventory.calculate_daily_values()
                    
                    # Add to database
                    db.session.add(inventory)
                    print(f"Added inventory entry for {item.description}")
            
            # Commit all changes
            db.session.commit()
            print("\nInventory population completed successfully!")
            
    except Exception as e:
        print(f"Error populating inventory: {str(e)}")
        if 'db' in locals():
            db.session.rollback()

if __name__ == "__main__":
    populate_inventory() 