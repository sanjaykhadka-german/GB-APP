from app import app, db
from models.inventory import Inventory
from models.item_master import ItemMaster
from models.raw_material_stocktake import RawMaterialStocktake
from models.raw_material_report_table import RawMaterialReportTable
from models.usage_report_table import UsageReportTable
from sqlalchemy import text
from datetime import datetime, timedelta

def migrate_inventory():
    with app.app_context():
        try:
            print("Migrating inventory data...")
            
            # Drop existing tables
            db.session.execute(text("DROP TABLE IF EXISTS inventory"))
            db.session.execute(text("DROP TABLE IF EXISTS raw_material_report_table"))
            db.session.execute(text("DROP TABLE IF EXISTS usage_report_table"))
            db.session.commit()
            
            # Create new tables
            db.create_all()
            
            # Get all raw material items
            raw_materials = ItemMaster.query.filter(
                ~ItemMaster.item_code.like('%.%'),  # Exclude items with dots (WIP)
                ~ItemMaster.item_code.like('%WIP%')  # Exclude WIP items
            ).all()
            
            # Get all weeks from stocktake
            weeks = db.session.query(RawMaterialStocktake.week_commencing).distinct().all()
            
            # For each week and raw material
            for week in weeks:
                week_commencing = week[0]
                print(f"Processing week {week_commencing}...")
                
                for rm in raw_materials:
                    # Get stocktake data
                    stocktake = RawMaterialStocktake.query.filter_by(
                        week_commencing=week_commencing,
                        item_code=rm.item_code
                    ).first()
                    
                    if stocktake:
                        # Create inventory record
                        inventory = Inventory(
                            week_commencing=week_commencing,
                            item_id=rm.id,
                            category_id=rm.category_id,
                            price_per_kg=rm.price_per_kg or 0.00,
                            required_total_production=0.00,  # Will be updated later
                            value_required_rm=0.00,  # Will be updated later
                            current_stock=stocktake.current_stock,
                            required_for_plan=0.00,  # Will be updated later
                            variance_week=0.00,  # Will be updated later
                            kg_required=0.00,  # Will be updated later
                            variance=0.00,  # Will be updated later
                            to_be_ordered=0.00,  # Will be calculated later
                            closing_stock=0.00  # Will be calculated later
                        )
                        
                        db.session.add(inventory)
            
            db.session.commit()
            print("Inventory data migration completed successfully!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate_inventory() 