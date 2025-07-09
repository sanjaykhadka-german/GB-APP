from app import app
from database import db
from models.inventory import Inventory
from models.raw_material_report_table import RawMaterialReportTable
from models.usage_report_table import UsageReportTable
from models.item_master import ItemMaster
from models.item_type import ItemType

def populate_inventory():
    with app.app_context():
        try:
            # Clear existing data
            db.session.query(Inventory).delete()
            db.session.commit()
            
            # Get RM type ID
            rm_type = ItemType.query.filter_by(type_name='RM').first()
            if not rm_type:
                print("Error: RM item type not found")
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
                    
                    print("Creating inventory record...")
                    
                    # Create inventory record
                    inventory = Inventory(
                        week_commencing=week_commencing,
                        item_id=raw_material.id,
                        category_id=raw_material.category_id or 1,  # Default to category 1 if none
                        price_per_kg=raw_material.price_per_kg or 0.00,
                        required_total_production=report.required_total_production,
                        value_required_rm=report.value_required_rm,
                        current_stock=report.current_stock,
                        required_for_plan=report.required_for_plan,
                        variance_week=report.variance_week,
                        kg_required=report.kg_required,
                        variance=report.variance,
                        to_be_ordered=0.00,  # Will be calculated later
                        closing_stock=0.00  # Will be calculated later
                    )
                    db.session.add(inventory)
                
                db.session.commit()
                print(f"Completed week: {week_commencing}")
            
            print("\nFinal count:")
            print(f"Inventory Records: {Inventory.query.count()}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    populate_inventory() 