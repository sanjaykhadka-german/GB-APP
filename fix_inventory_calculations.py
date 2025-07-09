#!/usr/bin/env python3
"""
Fix inventory table calculations based on raw material reports and stocktake data
"""

from app import create_app
from database import db
from sqlalchemy import text
from models.inventory import Inventory
from models.raw_material_report_table import RawMaterialReportTable
from models.raw_material_stocktake import RawMaterialStocktake
from models.item_master import ItemMaster
from models.category import Category

def fix_inventory_calculations():
    """Update inventory table with correct calculations"""
    app = create_app()
    
    with app.app_context():
        print("Fixing inventory table calculations...")
        
        # First, delete all records from inventory table but keep the table structure
        db.session.execute(text("DELETE FROM inventory"))
        db.session.commit()
        
        print("Cleared existing inventory records...")
        
        # Get all unique week_commencing dates from raw_material_report
        week_dates = db.session.query(RawMaterialReportTable.week_commencing).distinct().all()
        
        if not week_dates:
            print("No data found in raw_material_report_table!")
            return
            
        print(f"Found {len(week_dates)} weeks to process")
        
        for week_date in week_dates:
            week_commencing = week_date[0]
            print(f"\nProcessing week commencing: {week_commencing}")
            
            # Get all raw materials for this week
            raw_materials = db.session.query(
                RawMaterialReportTable.item_id,
                RawMaterialReportTable.required_total_production,
                ItemMaster.item_code,
                ItemMaster.description,
                ItemMaster.category_id,
                ItemMaster.price_per_kg,
                ItemMaster.supplier_name,
                Category.name.label('category_name')
            ).join(
                ItemMaster,
                RawMaterialReportTable.item_id == ItemMaster.id
            ).join(
                Category,
                ItemMaster.category_id == Category.id
            ).filter(
                RawMaterialReportTable.week_commencing == week_commencing
            ).all()
            
            print(f"Found {len(raw_materials)} raw materials for week {week_commencing}")
            
            for rm in raw_materials:
                # Get current stock from raw_material_stocktake
                stocktake = RawMaterialStocktake.query.filter_by(
                    item_code=rm.item_code
                ).order_by(
                    RawMaterialStocktake.week_commencing.desc()
                ).first()
                
                current_stock = stocktake.current_stock if stocktake else 0
                
                # Calculate required values
                required_total = float(rm.required_total_production or 0)
                value_required = (required_total * float(rm.price_per_kg)) if rm.price_per_kg else 0
                
                try:
                    # Create new inventory entry
                    inventory = Inventory(
                        week_commencing=week_commencing,
                        item_id=rm.item_id,
                        required_total=required_total,
                        category=rm.category_name,
                        price_per_kg=float(rm.price_per_kg) if rm.price_per_kg else 0,
                        value_required=value_required,
                        current_stock=float(current_stock),
                        supplier_name=rm.supplier_name,
                        # Set fixed values for daily columns for now
                        monday=0,
                        tuesday=0,
                        wednesday=0,
                        thursday=0,
                        friday=0,
                        saturday=0,
                        sunday=0
                    )
                    
                    # Calculate required_for_plan (sum of daily values)
                    required_for_plan = sum([
                        inventory.monday or 0,
                        inventory.tuesday or 0,
                        inventory.wednesday or 0,
                        inventory.thursday or 0,
                        inventory.friday or 0,
                        inventory.saturday or 0,
                        inventory.sunday or 0
                    ])
                    
                    inventory.required_for_plan = required_for_plan
                    
                    # Calculate variances
                    inventory.variance_for_week = float(current_stock) - required_for_plan
                    inventory.variance = float(current_stock) - required_total
                    
                    # Add to session
                    db.session.add(inventory)
                    
                except Exception as e:
                    print(f"Error processing item {rm.item_code}: {str(e)}")
                    continue
            
            # Commit after processing each week
            try:
                db.session.commit()
                print(f"Successfully processed {len(raw_materials)} raw materials for week {week_commencing}")
            except Exception as e:
                db.session.rollback()
                print(f"Error processing week {week_commencing}: {str(e)}")

if __name__ == '__main__':
    fix_inventory_calculations() 