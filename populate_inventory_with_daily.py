"""
Enhanced inventory population script with daily data
"""
from app import app, db
from models.item_master import ItemMaster
from models.item_type import ItemType
from models.raw_material_report_table import RawMaterialReportTable
from models.usage_report_table import UsageReportTable
from models.inventory import Inventory

def populate_inventory_with_daily():
    with app.app_context():
        try:
            print("Starting inventory population...")
            
            # Get raw material type
            rm_type = ItemType.query.filter_by(type_name='Raw Material').first()
            if not rm_type:
                print("Error: Raw Material type not found")
                return
            
            # Get all raw materials
            raw_materials = ItemMaster.query.filter_by(item_type_id=rm_type.id).all()
            print(f"\nFound {len(raw_materials)} raw materials")
            
            # Get all weeks from raw material report
            weeks = db.session.query(RawMaterialReportTable.week_commencing).distinct().all()
            weeks = [week[0] for week in weeks]
            print(f"Found {len(weeks)} weeks")
            
            # Process each week
            for week_commencing in weeks:
                print(f"\nProcessing week: {week_commencing}")
                
                # Process each raw material
                for raw_material in raw_materials:
                    print(f"\nProcessing raw material: {raw_material.item_code} - {raw_material.description}")
                    
                    # Get raw material report
                    report = RawMaterialReportTable.query.filter_by(
                        week_commencing=week_commencing,
                        item_id=raw_material.id
                    ).first()
                    
                    if not report:
                        print("No report found, skipping...")
                        continue
                    
                    # Get usage report
                    usage = UsageReportTable.query.filter_by(
                        week_commencing=week_commencing,
                        item_id=raw_material.id
                    ).first()
                    
                    if not usage:
                        print("No usage found, skipping...")
                        continue
                    
                    # Create or update inventory entry
                    inventory = Inventory.query.filter_by(
                        week_commencing=week_commencing,
                        item_id=raw_material.id
                    ).first()
                    
                    if inventory:
                        inventory.required_total_production = usage.total_usage
                        inventory.value_required_rm = usage.total_usage * (raw_material.price_per_kg or 0)
                        inventory.required_for_plan = usage.total_usage
                        inventory.kg_required = usage.total_usage
                        if inventory.current_stock is not None:
                            inventory.variance_week = inventory.current_stock - usage.total_usage
                            inventory.variance = inventory.current_stock - usage.total_usage
                    else:
                        inventory = Inventory(
                            week_commencing=week_commencing,
                            item_id=raw_material.id,
                            required_total_production=usage.total_usage,
                            value_required_rm=usage.total_usage * (raw_material.price_per_kg or 0),
                            current_stock=0.00,
                            required_for_plan=usage.total_usage,
                            variance_week=0.00 - usage.total_usage,
                            kg_required=usage.total_usage,
                            variance=0.00 - usage.total_usage
                        )
                        db.session.add(inventory)
                    
                    db.session.commit()
                    print(f"Added/updated inventory for {raw_material.description}: {usage.total_usage:.2f} kg")
            
            print("\nInventory population completed successfully!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    populate_inventory_with_daily() 