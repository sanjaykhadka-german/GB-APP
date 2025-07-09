"""
Test script to debug daily population issues
"""
from app import app
from database import db
from models.inventory import Inventory
from models.raw_material_report_table import RawMaterialReportTable
from models.usage_report_table import UsageReportTable
from models.item_master import ItemMaster
from models.item_type import ItemType

def test_daily_populate():
    with app.app_context():
        try:
            print("Starting test...")
            
            # Check current inventory count
            current_count = Inventory.query.count()
            print(f"Current inventory records: {current_count}")
            
            # Get RM type ID
            rm_type = ItemType.query.filter_by(type_name='RM').first()
            if not rm_type:
                print("Error: RM item type not found")
                return
            
            print(f"RM type found: {rm_type.id}")
            
            # Get first few raw materials
            raw_materials = ItemMaster.query.filter_by(item_type_id=rm_type.id).limit(5).all()
            print(f"Found {len(raw_materials)} raw materials (testing first 5)")
            
            # Get first week
            week = db.session.query(RawMaterialReportTable.week_commencing).first()
            if not week:
                print("No weeks found in raw material report")
                return
            
            week_commencing = week[0]
            print(f"Testing week: {week_commencing}")
            
            # Test one raw material
            for raw_material in raw_materials:
                print(f"\nTesting: {raw_material.item_code} - {raw_material.description}")
                
                # Get raw material report
                report = RawMaterialReportTable.query.filter_by(
                    week_commencing=week_commencing,
                    item_id=raw_material.id
                ).first()
                
                if not report:
                    print("No report found")
                    continue
                
                print(f"Report found - Required: {report.required_total_production}")
                
                # Get usage report
                usage = UsageReportTable.query.filter_by(
                    week_commencing=week_commencing,
                    item_id=raw_material.id
                ).first()
                
                if usage:
                    print(f"Usage found - Mon: {usage.monday}, Tue: {usage.tuesday}")
                    daily_values = {
                        'monday': float(usage.monday or 0),
                        'tuesday': float(usage.tuesday or 0),
                        'wednesday': float(usage.wednesday or 0),
                        'thursday': float(usage.thursday or 0),
                        'friday': float(usage.friday or 0),
                        'saturday': 0.00,
                        'sunday': 0.00
                    }
                else:
                    print("No usage found")
                    daily_values = {
                        'monday': 0.00, 'tuesday': 0.00, 'wednesday': 0.00,
                        'thursday': 0.00, 'friday': 0.00, 'saturday': 0.00, 'sunday': 0.00
                    }
                
                print(f"Daily values: {daily_values}")
                
                # Try to create inventory record
                try:
                    inventory = Inventory(
                        week_commencing=week_commencing,
                        item_id=raw_material.id,
                        category_id=raw_material.category_id or 1,
                        price_per_kg=raw_material.price_per_kg or 0.00,
                        required_total_production=report.required_total_production,
                        value_required_rm=report.value_required_rm,
                        current_stock=report.current_stock,
                        required_for_plan=report.required_for_plan,
                        variance_week=report.variance_week,
                        kg_required=report.kg_required,
                        variance=report.variance,
                        to_be_ordered=0.00,
                        closing_stock=0.00,
                        monday=daily_values['monday'],
                        tuesday=daily_values['tuesday'],
                        wednesday=daily_values['wednesday'],
                        thursday=daily_values['thursday'],
                        friday=daily_values['friday'],
                        saturday=daily_values['saturday'],
                        sunday=daily_values['sunday']
                    )
                    
                    print("Inventory object created successfully")
                    
                    # Test the calculation method
                    total = inventory.calculate_weekly_total()
                    print(f"Weekly total calculation: {total}")
                    
                    # Don't commit yet, just test
                    # db.session.add(inventory)
                    # db.session.commit()
                    
                except Exception as e:
                    print(f"Error creating inventory: {str(e)}")
                    
                break  # Only test first found item
            
            print("Test completed successfully!")
            
        except Exception as e:
            print(f"Test error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_daily_populate() 